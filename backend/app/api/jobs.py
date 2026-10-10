"""Persistent investigation jobs, claimed atomically by the separate worker."""
import time, uuid, hashlib
from fastapi import APIRouter, HTTPException
from sqlalchemy import String, Float, JSON, select, update, text
from sqlalchemy.orm import Mapped, mapped_column, Session
from ..core.database import Base, engine, owner_id, initialize_schema
from ..schemas.investigation import InvestigationRequest

class Job(Base):
    __tablename__ = 'investigation_jobs'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created: Mapped[float] = mapped_column(Float)
    lease_until: Mapped[float] = mapped_column(Float, default=0)

initialize_schema()
router = APIRouter(prefix='/jobs', tags=['Investigation jobs'])

@router.get('')
def list_jobs():
    with Session(engine) as db:
        jobs = db.scalars(select(Job).where(Job.owner == owner_id.get()).order_by(Job.created.desc()).limit(20)).all()
        return [{'id': job.id, 'status': job.status, 'question': job.payload.get('question'),
                 'result': {'investigation_id': job.result.get('investigation_id')} if job.result else None,
                 'error': job.error, 'created_at': job.created} for job in jobs]

@router.post('', status_code=202)
def submit_job(payload: InvestigationRequest):
    with Session(engine) as db, db.begin():
        if engine.dialect.name == 'sqlite':
            db.execute(text('BEGIN IMMEDIATE'))
        else:
            # Serialize admission for one owner without blocking other workspaces.
            lock = int.from_bytes(hashlib.sha256(owner_id.get().encode()).digest()[:8], 'big', signed=True)
            db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key':lock})
        pending = db.scalars(select(Job.id).where(Job.owner == owner_id.get(), Job.status.in_(['queued', 'running']))).all()
        if len(pending) >= 3:
            raise HTTPException(429, 'Three investigations are already pending. Wait or cancel a job.')
        job = Job(id='job-' + uuid.uuid4().hex, owner=owner_id.get(), status='queued', payload=payload.model_dump(mode='json'), created=time.time())
        db.add(job)
        return {'id': job.id, 'status': 'queued', 'poll_url': f'/api/jobs/{job.id}'}

@router.get('/{job_id}')
def get_job(job_id: str):
    with Session(engine) as db:
        job = db.get(Job, job_id)
        if not job or job.owner != owner_id.get():
            raise HTTPException(404, 'Job not found')
        return {'id': job.id, 'status': job.status, 'result': job.result, 'error': job.error, 'created_at': job.created}

@router.post('/{job_id}/cancel')
def cancel_job(job_id: str):
    with Session(engine) as db, db.begin():
        row = db.execute(update(Job).where(Job.id == job_id, Job.owner == owner_id.get(), Job.status.in_(['queued', 'running'])).values(status='cancelled'))
        if not row.rowcount:
            raise HTTPException(409, 'Job is absent or already finished.')
    return {'id': job_id, 'status': 'cancelled'}

def claim_job():
    with engine.connect() as conn:
        if engine.dialect.name == 'sqlite':
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.begin()
        # Expired running jobs fail visibly; no automatic repeated provider charges.
        conn.execute(update(Job).where(Job.status == 'running', Job.lease_until < time.time()).values(status='error', error='Worker interrupted. Submit again to retry.'))
        row = conn.execute(select(Job).where(Job.status == 'queued').order_by(Job.created).with_for_update(skip_locked=True).limit(1)).mappings().first()
        if row:
            conn.execute(update(Job).where(Job.id == row['id']).values(status='running', lease_until=time.time() + 900))
        conn.commit()
        return dict(row) if row else None

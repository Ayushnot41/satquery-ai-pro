"""Integration smoke test against a disposable CI PostgreSQL database."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import uuid

url = os.environ.get('POSTGRES_SMOKE_URL', '')
if not url.startswith('postgresql+psycopg://') or not url.endswith('/satquery_ci'):
    raise SystemExit('Set POSTGRES_SMOKE_URL to the disposable satquery_ci database.')
backend = Path(__file__).resolve().parents[1] / 'backend'
os.environ.update(DATABASE_URL=url, ENVIRONMENT='test', DEMO_MODE='true', VLM_BACKEND='demo')
sys.path.insert(0, str(backend))
os.chdir(backend)

# API and worker may both initialize a fresh database during a deployment.
children = [subprocess.Popen([sys.executable, '-c', 'import app.api.jobs; import app.core.guard'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(3)]
for child in children:
    _, error = child.communicate(timeout=60)
    if child.returncode:
        raise SystemExit(error)

from sqlalchemy import delete
from app.core.database import DurableStore, Record, engine, owner_id
from app.api.jobs import Job, submit_job, get_job
from app.schemas.investigation import InvestigationRequest
from app.worker import process_one

owner = 'postgres-smoke-' + uuid.uuid4().hex
context = owner_id.set(owner)
try:
    store = DurableStore('smoke')
    store['record'] = {'value': 'persisted'}
    assert DurableStore('smoke')['record']['value'] == 'persisted'
    other = owner_id.set(owner + '-other')
    try:
        assert 'record' not in DurableStore('smoke')
    finally:
        owner_id.reset(other)
    job = submit_job(InvestigationRequest(question='Describe the illustrative scene', imagery_ids=['demo-construction-before']))
    assert asyncio.run(process_one())
    completed = get_job(job['id'])
    assert completed['status'] == 'complete', completed['error']
    assert completed['result']['investigation_id'] in DurableStore('investigations')
    print('PostgreSQL first boot, ownership, persistence, and worker completion passed.')
finally:
    with engine.begin() as connection:
        connection.execute(delete(Job).where(Job.owner == owner))
        connection.execute(delete(Record).where(Record.owner == owner))
    owner_id.reset(context)

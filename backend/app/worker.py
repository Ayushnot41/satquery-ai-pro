"""Run with python -m app.worker. Pending work survives API restarts."""
import asyncio, logging
from sqlalchemy import update
from .api.jobs import Job, claim_job
from .api.investigation import execute_investigation
from .schemas.investigation import InvestigationRequest
from .core.database import engine, owner_id, Record
from fastapi import HTTPException

async def process_one():
    job = claim_job()
    if not job:
        return False
    token = owner_id.set(job['owner'])
    try:
        response = await asyncio.wait_for(execute_investigation(InvestigationRequest.model_validate(job['payload']), persist=False), timeout=840)
        values = {'status': 'complete' if response.status == 'complete' else 'error', 'result': response.model_dump(mode='json')}
    except HTTPException as exc:
        values = {'status': 'error', 'error': str(exc.detail)}
    except Exception:
        logging.exception('Investigation worker failed for job %s', job['id'])
        values = {'status': 'error', 'error': 'Investigation failed. Check provider configuration and input imagery.'}
    finally:
        owner_id.reset(token)
    with engine.begin() as conn:
        changed = conn.execute(update(Job).where(Job.id == job['id'], Job.status == 'running').values(**values))
        if changed.rowcount and values.get('result'):
            result = values['result']
            conn.execute(Record.__table__.insert().values(namespace='investigations', owner=job['owner'],
                         key=result['investigation_id'], value=result))
    return True

async def main():
    while True:
        try:
            if not await process_one():
                await asyncio.sleep(1)
        except Exception:
            logging.exception('Worker queue unavailable')
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())

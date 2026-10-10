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
os.environ.update(DATABASE_URL=url, ENVIRONMENT='test', DEMO_MODE='true', VLM_BACKEND='demo', DEVELOPMENT_VERIFICATION_CODES='true', COOKIE_SECURE='false')
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
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.api import auth
from app.core.config import settings

owner = 'postgres-smoke-' + uuid.uuid4().hex
context = owner_id.set(owner)
identity_records = []
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
    phone = '+1555' + str(int(uuid.uuid4().hex[:7], 16)).zfill(9)
    with TestClient(app) as client:
        sent = client.post('/api/auth/otp/send', json={'phone':phone, 'purpose':'login'})
        assert sent.status_code == 200, sent.text
        identity_records.extend([('phone_sends', auth.digest(phone)), ('challenges', 'otp:'+auth.digest(client.cookies.get(auth.OTP_COOKIE)))])
        result = client.post('/api/auth/otp/verify', json={'phone':phone, 'otp':sent.json()['development_code'], 'purpose':'login'})
        assert result.status_code == 200, result.text
        data = result.json()
        assert data['user']['email'] is None and data['user']['phone_verified']
        identity_records.extend([('users', 'id:'+data['user']['id']), ('verified_phones', auth.digest(phone)), ('sessions', auth.digest(data['access_token']))])
        assert client.get('/api/auth/me').json()['user']['id'] == data['user']['id']
        # Exercise PostgreSQL JSON subject lookup for an existing Google identity.
        subject = uuid.uuid4().hex
        email = subject + '@gmail.com'
        legacy = auth.create_user(email, 'CI Google', google_sub=subject, email_verified=True)
        identity_records.extend([('users', email), ('google_identities', subject)])
        with patch.object(settings, 'google_client_id', 'ci.apps.googleusercontent.com'):
            nonce = client.post('/api/auth/google/nonce', json={}).json()['nonce']
            identity_records.append(('challenges', 'google:'+auth.digest(nonce)))
            with patch('google.oauth2.id_token.verify_oauth2_token', return_value={'sub':subject,'email':email,'email_verified':True,'nonce':nonce}):
                response = client.post('/api/auth/google', json={'credential':'mocked-ci-token'})
            assert response.status_code == 200, response.text
            assert response.json()['user']['id'] == legacy['id']
            identity_records.append(('sessions', auth.digest(response.json()['access_token'])))
    print('PostgreSQL phone signup, sessions, and Google subject lookup passed (mock providers).')
finally:
    with engine.begin() as connection:
        connection.execute(delete(Job).where(Job.owner == owner))
        connection.execute(delete(Record).where(Record.owner == owner))
        for namespace, key in identity_records:
            connection.execute(delete(Record).where(Record.namespace == namespace, Record.owner == 'system', Record.key == key))
    owner_id.reset(context)

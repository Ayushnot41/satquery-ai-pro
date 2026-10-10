import io, time, uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app
from app.api.auth import USERS, SESSIONS, CHALLENGES, digest, make_challenge
from app.core.config import settings
from app.core.database import engine, DurableStore, owner_id
from app.core.security import ensure_safe_path

def account(client):
    email=f'{uuid.uuid4().hex}@example.test'
    response=client.post('/api/auth/register',json={'name':'Test analyst','email':email,'password':'Correct horse battery 47','clearance_level':'LEVEL_4_TOP_SECRET'})
    assert response.status_code==200,response.text
    cookie = response.headers.get('set-cookie', '').lower()
    assert 'httponly' in cookie and 'samesite=lax' in cookie
    return email,response.json()

def test_password_session_and_clearance():
    with TestClient(app) as client:
        email,data=account(client)
        assert data['user']['clearance_level']=='PUBLIC'
        assert not data['user']['email_verified']
        assert USERS[email]['password_hash'].startswith('$argon2id$')
        assert 'password_hash' not in data['user']
        assert 'satquery_session' in client.cookies
        assert client.get('/api/auth/me',headers={'Authorization':'Bearer invalid'}).status_code==401
        assert client.post('/api/auth/login',json={'email':'nobody@example.test','password':'incorrect'}).status_code==401
        assert 'nobody@example.test' not in USERS
        client.post('/api/auth/logout',json={})
        assert client.get('/api/auth/me').status_code==401
        assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+data['access_token']}).status_code==401

def test_expired_session_rejected():
    with TestClient(app) as client:
        _,data=account(client)
        record=SESSIONS[digest(data['access_token'])]
        record['expires']=time.time()-1
        SESSIONS[digest(data['access_token'])]=record
        assert client.get('/api/auth/me').status_code==401

def test_verification_is_single_use_and_no_magic_otp():
    with TestClient(app) as client:
        email,data=account(client)
        phone='+1555'+str(int(uuid.uuid4().hex[:7],16)).zfill(9)
        sent=client.post('/api/auth/otp/send',json={'phone':phone}).json()
        code=sent['development_code']
        wrong=str((int(code)+1)%1000000).zfill(6)
        assert client.post('/api/auth/otp/verify',json={'phone':phone,'otp':wrong}).status_code==400
        body={'phone':phone,'otp':code}
        first=client.post('/api/auth/otp/verify',json=body)
        assert first.status_code==200
        assert first.json()['user']['clearance_level']=='PUBLIC'
        assert client.post('/api/auth/otp/verify',json=body).status_code==400
        sent=client.post('/api/auth/email/send',json={}).json()
        verify={'token':sent['development_token']}
        assert client.post('/api/auth/email/verify',json=verify).json()['verified']
        assert client.post('/api/auth/email/verify',json=verify).status_code==400

def test_otp_attempt_limit_and_expiry():
    with TestClient(app) as client:
        email,data=account(client)
        phone='+1555'+str(int(uuid.uuid4().hex[:7],16)).zfill(9)
        sent=client.post('/api/auth/otp/send',json={'phone':phone}).json()
        code=sent['development_code']
        wrong=str((int(code)+1)%1000000).zfill(6)
        for _ in range(5):
            assert client.post('/api/auth/otp/verify',json={'phone':phone,'otp':wrong}).status_code==400
        assert client.post('/api/auth/otp/verify',json={'phone':phone,'otp':code}).status_code==400

def test_password_reset_revokes_sessions():
    with TestClient(app) as client:
        email,data=account(client)
        sent=client.post('/api/auth/password/forgot',json={'email':email}).json()
        response=client.post('/api/auth/password/reset',json={'token':sent['development_token'],'password':'Another strong password 85'})
        assert response.status_code==200
        assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+data['access_token']}).status_code==401
        assert client.post('/api/auth/login',json={'email':email,'password':'Correct horse battery 47'}).status_code==401
        assert client.post('/api/auth/login',json={'email':email,'password':'Another strong password 85'}).status_code==200

def test_csrf_and_auth_rate_limit():
    with TestClient(app) as client:
        assert client.post('/api/auth/guest-token',headers={'Origin':'https://untrusted.example'},json={}).status_code==403
        for _ in range(15):
            response=client.post('/api/auth/login',json={'email':'missing@example.test','password':'wrong'})
            assert response.status_code==401
        assert client.post('/api/auth/login',json={'email':'missing@example.test','password':'wrong'}).status_code==429

def test_private_uploads_and_persistence():
    image=io.BytesIO();Image.new('RGB',(24,24),(22,150,80)).save(image,format='PNG')
    with TestClient(app) as first,TestClient(app) as second:
        _,owner=account(first);account(second)
        response=first.post('/api/imagery/upload',files={'file':('actual.png',image.getvalue(),'image/png')})
        assert response.status_code==200,response.text
        data=response.json();image_id=data['id']
        assert data['metadata']['geo']['crs'] is None
        assert data['metadata']['satellite'] is None
        assert first.get(data['preview_url']).status_code==200
        assert second.get(data['preview_url']).status_code==404
        assert second.get('/api/imagery/'+image_id).status_code==404
        assert second.get('/api/imagery').json()==[]
        context=owner_id.set(owner['user']['id'])
        try:
            # A fresh store instance reads the persisted record.
            assert DurableStore('imagery')[image_id]['id']==image_id
        finally:owner_id.reset(context)
        assert first.post('/api/imagery/upload',files={'file':('fake.png',b'not an image','image/png')}).status_code==422
        assert first.post('/api/investigate',json={'question':'What changed?','imagery_ids':[image_id]}).status_code==503
    with TestClient(app) as anonymous:
        assert anonymous.get(data['preview_url']).status_code==401
        assert anonymous.post('/api/imagery/upload',files={'file':('actual.png',image.getvalue(),'image/png')}).status_code==401

def test_paths_unknown_images_and_tile_semantics(tmp_path):
    base=tmp_path/'uploads';base.mkdir()
    with pytest.raises(ValueError):ensure_safe_path('../uploads-evil/data',str(base))
    with TestClient(app) as client:
        account(client)
        response=client.post('/api/investigate',json={'question':'Describe this','imagery_ids':['demo-../../private']})
        assert response.status_code==404
        response=client.get('/api/nasa-tile',params={'layer':'MODIS_Terra_NDVI_8Day','date':'2024-01-15','z':12,'x':0,'y':0})
        assert response.status_code==422
        assert client.get('/api/investigate/missing/geojson').status_code==404

def test_production_blocks_demo_codes_and_guests(monkeypatch):
    monkeypatch.setattr(settings,'environment','production')
    monkeypatch.setattr(settings,'cookie_secure',True)
    monkeypatch.setattr(settings,'development_verification_codes',False)
    monkeypatch.setattr(settings,'allow_demo_guest',False)
    monkeypatch.setattr(settings,'cors_origins','https://satquery.example')
    with TestClient(app) as client:
        assert client.post('/api/auth/guest-token',json={}).status_code==403
        assert not client.get('/api/auth/config').json()['development_codes']

@pytest.mark.asyncio
async def test_job_execution_isolation_and_cancel():
    import httpx
    from app.worker import process_one
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as first, httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as second:
        await first.post('/api/auth/guest-token',json={});await second.post('/api/auth/guest-token',json={})
        payload={'question':'Describe this scene','imagery_ids':['demo-construction-before']}
        response=await first.post('/api/jobs',json=payload)
        assert response.status_code==202
        path=response.json()['poll_url']
        assert (await second.get(path)).status_code==404
        assert await process_one()
        result=(await first.get(path)).json()
        assert result['status']=='complete',result
        assert result['result']['provenance']['mode']=='simulation'
        assert (await first.get('/api/investigate')).json()
        queued=(await first.post('/api/jobs',json=payload)).json()
        assert (await first.post(queued['poll_url']+'/cancel')).json()['status']=='cancelled'
        assert not await process_one()

"""Authentication contracts: no real provider traffic or billable SMS."""
import secrets
import time
import uuid
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import auth, phone
from app.core import sms
from app.core.config import settings
from app.core.database import DurableStore
from tests.test_pro_security import account


def number():
    return '+1555' + ''.join(str(secrets.randbelow(10)) for _ in range(7))


def allow_resend(value):
    store = DurableStore('phone_sends', global_scope=True)
    row = store[auth.digest(value)]
    store[auth.digest(value)] = {**row, 'sent_at': time.time() - 31}


def send(client, value, purpose='login'):
    result = client.post('/api/auth/otp/send', json={'phone': value, 'purpose': purpose})
    assert result.status_code == 200, result.text
    return result.json()


def verify(client, value, code, purpose='login'):
    return client.post('/api/auth/otp/verify', json={'phone': value, 'otp': code, 'purpose': purpose})


def test_phone_signup_login_without_email_and_legacy_session():
    value = number()
    with TestClient(app) as client:
        code = send(client, value)['development_code']
        assert not auth.PHONES.get(auth.digest(value))
        first = verify(client, value, code)
        assert first.status_code == 200, first.text
        user = first.json()['user']
        assert first.json()['created']
        assert user['email'] is None and user['phone_verified'] and not user['email_verified']
        assert '_key' not in user and user['clearance_level'] == 'PUBLIC'
        assert client.post('/api/auth/email/send', json={}).status_code == 400
        assert client.get('/api/auth/me').json()['user']['id'] == user['id']
        assert verify(client, value, code).status_code == 400
        client.post('/api/auth/logout', json={})
        allow_resend(value)
        second = verify(client, value, send(client, value)['development_code']).json()
        assert not second['created'] and second['user']['id'] == user['id']
        # Previously issued email-keyed sessions still resolve.
        email, _ = account(client)
        token = secrets.token_urlsafe(32)
        auth.SESSIONS[auth.digest(token)] = {'email': email, 'expires': time.time()+300}
        assert client.get('/api/auth/me', headers={'Authorization':'Bearer '+token}).json()['user']['email'] == email


def test_phone_challenge_cannot_cross_browser_phone_or_purpose():
    value = number()
    with TestClient(app) as first, TestClient(app) as other:
        code = send(first, value)['development_code']
        assert verify(other, value, code).status_code == 400
        assert verify(first, number(), code).status_code == 400
        account(first)
        assert verify(first, value, code, 'verification').status_code == 400
        assert verify(first, value, code).status_code == 200


def test_phone_code_expiry_and_resend_invalidate_old_flow():
    value = number()
    with TestClient(app) as client:
        code = send(client, value)['development_code']
        old_cookie = client.cookies.get(auth.OTP_COOKIE)
        limited = client.post('/api/auth/otp/send', json={'phone':value,'purpose':'login'})
        assert limited.status_code == 429 and int(limited.headers['Retry-After']) > 0
        allow_resend(value)
        replacement = send(client, value)['development_code']
        assert not auth.CHALLENGES.get('otp:'+auth.digest(old_cookie))
        key = 'otp:'+auth.digest(client.cookies.get(auth.OTP_COOKIE))
        row = auth.CHALLENGES[key]
        auth.CHALLENGES[key] = {**row, 'expires': time.time()-1}
        assert verify(client, value, replacement).status_code == 400
        assert not auth.PHONES.get(auth.digest(value))


def test_phone_hourly_limit():
    value = number()
    with TestClient(app) as client:
        for _ in range(5):
            send(client, value)
            allow_resend(value)
        assert client.post('/api/auth/otp/send',json={'phone':value,'purpose':'login'}).status_code == 429


def test_sms_disabled_does_not_contact_provider(monkeypatch):
    monkeypatch.setattr(settings, 'development_verification_codes', False)
    monkeypatch.setattr(settings, 'sms_enabled', False)
    async def forbidden(*args, **kwargs):
        pytest.fail('Disabled SMS must not call a provider')
    monkeypatch.setattr(phone, 'verify_request', forbidden)
    with TestClient(app) as client:
        assert not client.get('/api/auth/config').json()['sms_delivery']
        assert client.post('/api/auth/otp/send',json={'phone':number(),'purpose':'login'}).status_code == 503


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings, 'development_verification_codes', False)
    monkeypatch.setattr(settings, 'sms_enabled', True)
    monkeypatch.setattr(settings, 'twilio_api_key', 'SKtest')
    monkeypatch.setattr(settings, 'twilio_api_secret', 'test-secret-not-real')
    monkeypatch.setattr(settings, 'twilio_verify_service_sid', 'VAtest')
    calls = []
    state = {'status':'approved'}
    async def fake(resource, data):
        calls.append((resource, data))
        if resource == 'Verifications':
            state['phone'] = data['To']
            return {'sid':'VEtest', 'status':'pending'}
        return {'sid':state.get('sid','VEtest'), 'status':state['status'], 'to':state['phone']}
    monkeypatch.setattr(phone, 'verify_request', fake)
    return state, calls


def test_twilio_signup_checks_exact_verification_and_is_single_use(provider):
    state, calls = provider
    value = number()
    with TestClient(app) as client:
        sent = send(client, value)
        assert 'development_code' not in sent
        assert verify(client, value, '123456').status_code == 200
        assert calls[-1] == ('VerificationCheck', {'VerificationSid':'VEtest','Code':'123456'})
        assert verify(client, value, '123456').status_code == 400
        assert len(calls) == 2


@pytest.mark.parametrize('status,sid', [('pending','VEtest'),('approved','VEwrong')])
def test_provider_mismatch_never_creates_account(provider, status, sid):
    state, _ = provider
    state.update(status=status, sid=sid)
    value = number()
    with TestClient(app) as client:
        send(client, value)
        assert verify(client, value, '123456').status_code == 400
        assert not auth.PHONES.get(auth.digest(value))


def test_verified_phone_allowed_in_production(provider, monkeypatch):
    monkeypatch.setattr(settings,'environment','production')
    monkeypatch.setattr(settings,'cookie_secure',True)
    monkeypatch.setattr(settings,'allow_demo_guest',False)
    monkeypatch.setattr(settings,'cors_origins','https://testserver')
    value = number()
    with TestClient(app, base_url='https://testserver') as client:
        send(client,value)
        assert verify(client,value,'123456').status_code == 200
        result = client.post('/api/jobs',json={'question':'Describe this scene','imagery_ids':['demo-construction-before']})
        assert result.status_code == 202, result.text
        client.post(result.json()['poll_url']+'/cancel')


@pytest.mark.asyncio
@pytest.mark.parametrize('status,expected',[(401,503),(429,429),(404,400)])
async def test_provider_adapter_maps_errors_without_leaking_secrets(provider, monkeypatch, status, expected):
    real_client = httpx.AsyncClient
    def handler(request):
        assert request.url.host == 'verify.twilio.com'
        assert request.url.path == '/v2/Services/VAtest/VerificationCheck'
        return httpx.Response(status,json={'message':'provider secret diagnostic'})
    monkeypatch.setattr(sms.httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as caught:
        await sms.verify_request('VerificationCheck', {'Code':'123456','VerificationSid':'VEtest'})
    assert caught.value.status_code == expected
    assert 'secret' not in caught.value.detail


@pytest.fixture
def google(monkeypatch):
    from google.oauth2 import id_token
    monkeypatch.setattr(settings,'google_client_id','test.apps.googleusercontent.com')
    claims = {'sub':uuid.uuid4().hex,'email':uuid.uuid4().hex+'@gmail.com','email_verified':True,'name':'Google member'}
    def fake(credential, request, audience):
        assert audience == settings.google_client_id
        return dict(claims)
    monkeypatch.setattr(id_token,'verify_oauth2_token',fake)
    return claims


def google_login(client, claims):
    response=client.post('/api/auth/google/nonce',json={})
    assert response.status_code == 200, response.text
    claims['nonce']=response.json()['nonce']
    return client.post('/api/auth/google',json={'credential':'test-credential'})


def test_google_signup_uses_subject_and_nonce_is_single_use(google):
    with TestClient(app) as client:
        first=google_login(client,google)
        assert first.status_code == 200, first.text
        assert first.json()['user']['email_verified']
        assert client.post('/api/auth/google',json={'credential':'test-credential'}).status_code == 401
        google['email']=uuid.uuid4().hex+'@gmail.com'
        second=google_login(client,google)
        assert second.json()['user']['id'] == first.json()['user']['id']


def test_google_wrong_browser_and_nonce_rejected(google):
    with TestClient(app) as client, TestClient(app) as other:
        google['nonce']=client.post('/api/auth/google/nonce',json={}).json()['nonce']
        assert other.post('/api/auth/google',json={'credential':'test-credential'}).status_code == 401
        google['nonce']='incorrect'
        assert client.post('/api/auth/google',json={'credential':'test-credential'}).status_code == 401


def test_google_does_not_merge_password_account_or_trust_third_party_email(google):
    with TestClient(app) as client:
        email,_=account(client)
        google['email']=email
        assert google_login(client,google).status_code == 409
        google['email']=uuid.uuid4().hex+'@example.test'
        result=google_login(client,google)
        assert result.status_code == 200, result.text
        assert not result.json()['user']['email_verified']


def test_google_legacy_account_keeps_id(google):
    legacy=auth.create_user(google['email'],'Legacy',google_sub=google['sub'],email_verified=True)
    with TestClient(app) as client:
        assert google_login(client,google).json()['user']['id'] == legacy['id']

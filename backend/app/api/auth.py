"""Verified identity with Argon2 passwords and revocable, durable sessions."""
from __future__ import annotations
import hashlib, hmac, secrets, smtplib, ssl, time, uuid
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool
from ..core.config import settings
from ..core.database import DurableStore, Record, engine
from ..core.identity import account_key, reference_key, identity_transaction, record_conditions, read_record
from ..core.sms import development_codes_enabled, sms_configured

router = APIRouter(prefix='/auth', tags=['Authentication & Security Clearance'])
USERS = DurableStore('users', global_scope=True)
SESSIONS = DurableStore('sessions', global_scope=True)
CHALLENGES = DurableStore('challenges', global_scope=True)
PHONES = DurableStore('verified_phones', global_scope=True)
GOOGLE_IDENTITIES = DurableStore('google_identities', global_scope=True)
hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash('timing-normalization-not-a-user-password')
COOKIE = 'satquery_session'
GOOGLE_COOKIE = 'satquery_google_nonce'
OTP_COOKIE = 'satquery_otp'

def digest(value: str) -> str:
    return hmac.new(settings.auth_pepper.encode(), value.encode(), hashlib.sha256).hexdigest()

def public_user(user):
    return {k: v for k, v in user.items() if k not in {'password_hash', 'google_sub', '_key'}}

def session_token(request: Request) -> str:
    auth = request.headers.get('authorization', '')
    return auth[7:] if auth.startswith('Bearer ') else request.cookies.get(COOKIE, '')

def resolve_user(request: Request):
    token = session_token(request)
    session = SESSIONS.get(digest(token)) if token else None
    if not session or session['expires'] <= time.time():
        return None
    return USERS.get(reference_key(session))

def require_user(request: Request):
    user = resolve_user(request)
    if user is None:
        raise HTTPException(401, 'Sign in to access this workspace.')
    return user

def new_user(email, name, **extra):
    user = dict(id=uuid.uuid4().hex, email=email, name=name, organization='', phone='', role='Analyst',
                clearance_level='PUBLIC', email_verified=False, phone_verified=False, google_verified=False,
                auth_providers=['email'], created_at=datetime.now(timezone.utc).isoformat(), guest=False)
    user.update(extra)
    user['_key'] = email or 'id:' + user['id']
    return user


def create_user(email, name, **extra):
    user = new_user(email, name, **extra)
    try:
        with Session(engine) as db, db.begin():
            db.add(Record(namespace='users', owner='system', key=account_key(user), value=user))
    except IntegrityError:
        raise HTTPException(409, 'Account already exists. Sign in or reset your password.')
    return user

def issue_session(user, response: Response):
    token = secrets.token_urlsafe(48)
    seconds = 3600 if user.get('guest') else settings.session_hours * 3600
    SESSIONS[digest(token)] = {'user_key': account_key(user), 'expires': time.time() + seconds, 'authenticated_at': time.time()}
    response.set_cookie(COOKIE, token, max_age=seconds, httponly=True, secure=settings.cookie_secure, samesite='lax', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'access_token': token, 'token_type': 'Bearer', 'expires_in_seconds': seconds, 'user': public_user(user)}

class EmailLoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1, max_length=256)
    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        import re
        value = value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a valid email address')
        return value

class EmailRegisterRequest(EmailLoginRequest):
    name: str = Field(min_length=2, max_length=120)
    organization: str = Field(default='', max_length=160)
    phone: str = Field(default='', max_length=16)
    clearance_level: str = 'PUBLIC'
    @field_validator('password')
    @classmethod
    def strong_password(cls, value):
        if len(value) < 12:
            raise ValueError('Use at least 12 characters')
        return value

class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=1, max_length=12000)
    client_id: str | None = None

class SendOtpRequest(BaseModel):
    phone: str = Field(pattern=r'^\+[1-9][0-9]{7,14}$')
    purpose: Literal['login', 'verification', 'clearance'] = 'verification'

    @field_validator('phone', mode='before')
    @classmethod
    def normalize_phone(cls, value):
        import re
        return re.sub(r'[\s()\-]', '', value) if isinstance(value, str) else value

class VerifyOtpRequest(SendOtpRequest):
    otp: str = Field(pattern=r'^\d{6}$')
    purpose: Literal['login', 'verification'] | None = None


def set_flow_cookie(response, name, value, seconds=300):
    response.set_cookie(name, value, max_age=seconds, httponly=True, secure=settings.cookie_secure, samesite='strict', path='/api/auth')

class EmailChallengeRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)

class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)

class PasswordResetRequest(VerifyEmailRequest):
    password: str = Field(min_length=12, max_length=256)

def make_challenge(key, email, code, ttl=900):
    CHALLENGES[key] = {'email': email, 'hash': digest(code), 'expires': time.time() + ttl, 'attempts': 0}

def consume_challenge(key, code):
    with engine.connect() as conn:
        if engine.dialect.name == 'sqlite':
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.begin()
        try:
            conditions = (Record.namespace == 'challenges', Record.owner == 'system', Record.key == key)
            row = conn.execute(select(Record.value).where(*conditions).with_for_update()).scalar_one_or_none()
            valid = row and row['expires'] > time.time() and row['attempts'] < 5 and hmac.compare_digest(row['hash'], digest(code))
            if valid:
                conn.execute(delete(Record).where(*conditions))
            elif row:
                conn.execute(update(Record).where(*conditions).values(value={**row, 'attempts': row['attempts'] + 1}))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    if not valid:
        raise HTTPException(400, 'Invalid, expired, or already used verification code.')
    return row['email']

def send_email(email, subject, token):
    if settings.development_verification_codes and settings.environment != 'production':
        return {'development_token': token, 'delivery': 'local-development-only'}
    if not settings.smtp_host:
        raise HTTPException(503, 'Email delivery is not configured. Contact the workspace administrator.')
    msg = EmailMessage()
    msg['From'], msg['To'], msg['Subject'] = settings.smtp_from, email, subject
    msg.set_content(f'{subject}\n\nEnter this single-use code in Satquery AI:\n{token}\n\nExpires in 15 minutes. If you did not request it, ignore this message.')
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or '')
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException):
        raise HTTPException(503, 'Email delivery is temporarily unavailable.')
    return {'delivery': 'email'}

@router.get('/config')
def auth_config():
    return {'public_preview': settings.environment == 'preview',
            'google_client_id': settings.google_client_id if settings.environment != 'preview' else None, 'demo_guest': settings.allow_demo_guest and settings.environment != 'production',
            'email_delivery': bool(settings.smtp_host), 'sms_delivery': sms_configured() and settings.environment != 'preview',
            'development_codes': development_codes_enabled()}

@router.post('/register')
def register_with_email(req: EmailRegisterRequest, response: Response):
    user = create_user(req.email, req.name, password_hash=hasher.hash(req.password))
    user['organization'] = req.organization
    USERS[req.email] = user
    return issue_session(user, response)

@router.post('/login')
def login_with_email(req: EmailLoginRequest, response: Response):
    user = USERS.get(req.email)
    valid = hasher.verify(req.password, user.get('password_hash', DUMMY_HASH) if user else DUMMY_HASH)
    if not user or not user.get('password_hash') or not valid:
        raise HTTPException(401, 'Invalid email or password.')
    return issue_session(user, response)

@router.post('/guest-token')
def guest_token(response: Response):
    if not settings.allow_demo_guest or settings.environment == 'production':
        raise HTTPException(403, 'Guest sessions are disabled.')
    email = f'guest-{uuid.uuid4().hex}@demo.invalid'
    user = create_user(email, 'Demo explorer')
    user.update(guest=True, role='Demo explorer', auth_providers=['guest'])
    USERS[email] = user
    return issue_session(user, response)

@router.post('/google/nonce')
def google_nonce(request: Request, response: Response):
    if not settings.google_client_id:
        raise HTTPException(503, 'Google sign-in is not configured.')
    old = request.cookies.get(GOOGLE_COOKIE)
    if old:
        CHALLENGES.pop('google:' + digest(old), None)
    nonce = secrets.token_urlsafe(32)
    make_challenge('google:' + digest(nonce), '', nonce, 300)
    set_flow_cookie(response, GOOGLE_COOKIE, nonce)
    return {'nonce': nonce}


@router.post('/google')
async def login_with_google(req: GoogleAuthRequest, request: Request, response: Response):
    if not settings.google_client_id:
        raise HTTPException(503, 'Google sign-in is not configured.')
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    try:
        info = await run_in_threadpool(id_token.verify_oauth2_token, req.credential, GoogleRequest(), settings.google_client_id)
        nonce = request.cookies.get(GOOGLE_COOKIE, '')
        if not info.get('email_verified') or not info.get('sub') or not info.get('email'):
            raise ValueError('Unverified identity')
        if not nonce or not isinstance(info.get('nonce'), str) or not hmac.compare_digest(nonce, info['nonce']):
            raise ValueError('Invalid login nonce')
    except Exception:
        raise HTTPException(401, 'Google identity could not be verified.')
    consume_challenge('google:' + digest(nonce), nonce)
    response.delete_cookie(GOOGLE_COOKIE, path='/api/auth')
    email, subject = info['email'].lower(), info['sub']
    # Google subject is stable even when the Google account's email changes.
    try:
        with identity_transaction('google:' + subject) as conn:
            binding = read_record(conn, 'google_identities', subject)
            user = read_record(conn, 'users', reference_key(binding)) if binding else None
            if not user:
                user = conn.execute(select(Record.value).where(Record.namespace == 'users', Record.owner == 'system', Record.value['google_sub'].as_string() == subject)).scalar_one_or_none()
            if not user:
                if read_record(conn, 'users', email):
                    raise HTTPException(409, 'An account exists with this email. Use its original sign-in method.')
                authoritative_email = email.endswith('@gmail.com') or bool(info.get('hd'))
                user = new_user(email, info.get('name') or 'Analyst', google_sub=subject,
                                email_verified=authoritative_email, google_verified=True, auth_providers=['google'])
                conn.execute(Record.__table__.insert().values(namespace='users', owner='system', key=account_key(user), value=user))
            if not binding:
                conn.execute(Record.__table__.insert().values(namespace='google_identities', owner='system', key=subject, value={'user_key': account_key(user)}))
    except IntegrityError as exc:
        raise HTTPException(409, 'This account was created concurrently. Try signing in again.') from exc
    return issue_session(user, response)

@router.post('/email/send')
def send_email_verification(request: Request):
    user = require_user(request)
    if user.get('guest'):
        raise HTTPException(403, 'Create an account to verify an email address.')
    if not user.get('email'):
        raise HTTPException(400, 'This account uses phone sign-in and has no email address to verify.')
    token = secrets.token_urlsafe(32)
    delivery = send_email(user['email'], 'Verify your Satquery AI email', token)
    make_challenge('email:' + digest(token), account_key(user), token)
    return {'message': 'Verification requested.', **delivery}

@router.post('/email/verify')
def verify_email(req: VerifyEmailRequest, request: Request):
    user = require_user(request)
    challenge = CHALLENGES.get('email:' + digest(req.token))
    if not challenge or challenge['email'] != account_key(user):
        raise HTTPException(400, 'Invalid verification code.')
    email = consume_challenge('email:' + digest(req.token), req.token)
    user = USERS[email]
    user['email_verified'] = True
    USERS[email] = user
    return {'user': public_user(user), 'verified': True}

@router.post('/password/forgot')
def forgot_password(req: EmailChallengeRequest):
    if not settings.smtp_host and not (settings.development_verification_codes and settings.environment != 'production'):
        raise HTTPException(503, 'Email delivery is not configured.')
    user = USERS.get(req.email.strip().lower())
    delivery = {}
    if user and user.get('password_hash'):
        token = secrets.token_urlsafe(32)
        delivery = send_email(user['email'], 'Reset your Satquery AI password', token)
        make_challenge('reset:' + digest(token), user['email'], token)
    return {'message': 'If the account is eligible, a reset code has been sent.', **({'development_token': delivery['development_token']} if 'development_token' in delivery else {})}

@router.post('/password/reset')
def reset_password(req: PasswordResetRequest, response: Response):
    email = consume_challenge('reset:' + digest(req.token), req.token)
    user = USERS[email]
    user['password_hash'] = hasher.hash(req.password)
    USERS[email] = user
    for key in list(SESSIONS):
        if reference_key(SESSIONS[key]) == email:
            del SESSIONS[key]
    response.delete_cookie(COOKIE, path='/')
    return {'message': 'Password updated. Sign in again on each device.'}

@router.post('/otp/send')
async def send_phone_otp(req: SendOtpRequest, request: Request, response: Response):
    from .phone import send_phone_otp as send_code
    return await send_code(req, request, response)


@router.post('/otp/verify')
async def verify_phone_otp(req: VerifyOtpRequest, request: Request, response: Response):
    from .phone import verify_phone_otp as verify_code
    return await verify_code(req, request, response)


@router.get('/me')
def get_current_user_profile(request: Request):
    user = require_user(request)
    return {'authenticated': True, 'guest': user.get('guest', False), 'user': public_user(user)}

@router.post('/logout')
def logout(request: Request, response: Response):
    SESSIONS.pop(digest(session_token(request)), None)
    response.delete_cookie(COOKIE, path='/')
    return {'status': 'success'}

"""Phone-first signup/sign-in, with browser-bound, single-use Verify challenges."""
import hmac
import secrets
import time
from fastapi import HTTPException, Request, Response
from sqlalchemy import delete, update
from .auth import (SendOtpRequest, VerifyOtpRequest, CHALLENGES, OTP_COOKIE, digest,
                   require_user, resolve_user, new_user, issue_session, set_flow_cookie)
from ..core.database import Record
from ..core.identity import account_key, reference_key, identity_transaction, record_conditions, read_record
from ..core.sms import development_codes_enabled, sms_configured, verify_request
from ..core.guard import rate_allowed

def phone_context(purpose, request, allow_verified=False):
    if purpose == 'login':
        return None
    user = require_user(request)
    if user.get('guest'):
        raise HTTPException(403, 'Create an account first.')
    if user.get('phone_verified') and not allow_verified:
        raise HTTPException(409, 'A verified phone is already attached. Phone replacement requires account recovery.')
    return user


async def send_phone_otp(req: SendOtpRequest, request: Request, response: Response):
    purpose = 'login' if req.purpose == 'login' else 'verification'
    user = phone_context(purpose, request)
    local = development_codes_enabled()
    if not local and not sms_configured():
        raise HTTPException(503, 'SMS sign-in is not enabled. Use another sign-in method.')
    phone_key = digest(req.phone)
    if not rate_allowed('sms-global-day', limit=100, seconds=86400):
        raise HTTPException(429, 'The workspace SMS limit has been reached. Try another sign-in method.')
    if not rate_allowed('sms-hour:' + phone_key, limit=5, seconds=3600):
        raise HTTPException(429, 'SMS limit reached for this number. Try again in an hour.')
    if user and not rate_allowed('sms-account:' + user['id'], limit=5, seconds=3600):
        raise HTTPException(429, 'SMS limit reached for this account. Try again in an hour.')
    flow = secrets.token_urlsafe(32)
    with identity_transaction('phone:' + phone_key) as conn:
        previous = read_record(conn, 'phone_sends', phone_key)
        if previous and previous['sent_at'] > time.time() - 30:
            wait = max(1, int(previous['sent_at'] + 30 - time.time()) + 1)
            raise HTTPException(429, f'Wait {wait} seconds before requesting another code.', headers={'Retry-After': str(wait)})
        conn.execute(delete(Record).where(*record_conditions('phone_sends', phone_key)))
        conn.execute(Record.__table__.insert().values(namespace='phone_sends', owner='system', key=phone_key,
            value={'sent_at': time.time(), 'flow': digest(flow)}))
    challenge = {'phone': req.phone, 'purpose': purpose, 'user_key': account_key(user) if user else None,
                 'expires': time.time() + 300, 'attempts': 0, 'provider': 'development' if local else 'twilio'}
    delivery = {}
    if local:
        code = f'{secrets.randbelow(1000000):06d}'
        challenge['hash'] = digest(code)
        delivery['development_code'] = code
    else:
        sent = await verify_request('Verifications', {'To': req.phone, 'Channel': 'sms'})
        if sent.get('status') != 'pending' or not str(sent.get('sid', '')).startswith('VE'):
            raise HTTPException(503, 'SMS verification could not be started. Try again later.')
        challenge['verification_sid'] = sent['sid']
    previous_cookie = request.cookies.get(OTP_COOKIE)
    if previous_cookie:
        CHALLENGES.pop('otp:' + digest(previous_cookie), None)
    CHALLENGES['otp:' + digest(flow)] = challenge
    set_flow_cookie(response, OTP_COOKIE, flow)
    return {'message': 'Enter the code to create your account or sign in.' if purpose == 'login' else 'Enter the code to verify your phone.',
            'expires_in_seconds': 300, 'retry_after_seconds': 30, **delivery}


async def verify_phone_otp(req: VerifyOtpRequest, request: Request, response: Response):
    purpose = req.purpose or ('verification' if resolve_user(request) else 'login')
    user = phone_context(purpose, request, allow_verified=True)
    flow = digest(request.cookies.get(OTP_COOKIE, ''))
    key, phone_key = 'otp:' + flow, digest(req.phone)
    with identity_transaction('phone:' + phone_key) as conn:
        challenge = read_record(conn, 'challenges', key)
        latest = read_record(conn, 'phone_sends', phone_key)
        valid = (challenge and latest and latest['flow'] == flow and challenge['phone'] == req.phone
                 and challenge['purpose'] == purpose and challenge['user_key'] == (account_key(user) if user else None)
                 and challenge['expires'] > time.time() and challenge['attempts'] < 5)
        if not valid:
            raise HTTPException(400, 'Invalid, expired, or already used verification code. Request a new code.')
        if challenge.get('checking_until', 0) > time.time():
            raise HTTPException(409, 'This code is already being checked. Please wait.')
        challenge = {**challenge, 'attempts': challenge['attempts'] + 1, 'checking_until': time.time() + 30}
        conn.execute(update(Record).where(*record_conditions('challenges', key)).values(value=challenge))
    try:
        if challenge['provider'] == 'development':
            approved = development_codes_enabled() and hmac.compare_digest(challenge['hash'], digest(req.otp))
        else:
            result = await verify_request('VerificationCheck', {'VerificationSid': challenge['verification_sid'], 'Code': req.otp})
            approved = result.get('status') == 'approved' and result.get('sid') == challenge['verification_sid'] and result.get('to') == req.phone
        if not approved:
            raise HTTPException(400, 'Invalid or expired SMS code.')
        with identity_transaction('phone:' + phone_key) as conn:
            pending = read_record(conn, 'challenges', key)
            latest = read_record(conn, 'phone_sends', phone_key)
            if not pending or not latest or latest['flow'] != flow or pending['expires'] <= time.time():
                raise HTTPException(400, 'This verification has expired or was replaced. Request a new code.')
            binding = read_record(conn, 'verified_phones', phone_key)
            created = False
            if purpose == 'login':
                user = read_record(conn, 'users', reference_key(binding)) if binding else None
                if binding and (not user or not user.get('phone_verified') or user.get('phone') != req.phone):
                    raise HTTPException(400, 'Phone sign-in is no longer available. Use your recovery sign-in method.')
                if not user:
                    user = new_user(None, 'Phone member', phone=req.phone, phone_verified=True, auth_providers=['phone'])
                    conn.execute(Record.__table__.insert().values(namespace='users', owner='system', key=account_key(user), value=user))
                    created = True
            else:
                if binding and reference_key(binding) != account_key(user):
                    raise HTTPException(409, 'This phone is already linked to an account. Sign in using that phone.')
                # Re-read inside the transaction to preserve concurrent profile changes.
                user = read_record(conn, 'users', account_key(user))
                if user.get('phone_verified') and user.get('phone') != req.phone:
                    raise HTTPException(409, 'A verified phone is already attached to this account.')
                user.update(phone=req.phone, phone_verified=True)
                user['auth_providers'] = list(dict.fromkeys([*user.get('auth_providers', []), 'phone']))
                conn.execute(update(Record).where(*record_conditions('users', account_key(user))).values(value=user))
            if not binding:
                conn.execute(Record.__table__.insert().values(namespace='verified_phones', owner='system', key=phone_key,
                    value={'user_key': account_key(user), 'email': user['email']}))
            conn.execute(delete(Record).where(*record_conditions('challenges', key)))
    except HTTPException:
        with identity_transaction('phone:' + phone_key) as conn:
            pending = read_record(conn, 'challenges', key)
            if pending:
                conn.execute(update(Record).where(*record_conditions('challenges', key)).values(value={**pending, 'checking_until': 0}))
        raise
    response.delete_cookie(OTP_COOKIE, path='/api/auth')
    return {'verified': True, 'created': created, **issue_session(user, response)}

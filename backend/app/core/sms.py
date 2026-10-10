"""Twilio Verify adapter. No SMS is sent without explicit configuration."""
import httpx
from fastapi import HTTPException
from .config import settings


def development_codes_enabled():
    return settings.development_verification_codes and settings.environment in ('development', 'test')


def sms_configured():
    credentials = (settings.twilio_api_key and settings.twilio_api_secret) or (settings.twilio_account_sid and settings.twilio_auth_token)
    return bool(settings.sms_enabled and credentials and settings.twilio_verify_service_sid)


async def verify_request(resource, data):
    if not sms_configured():
        raise HTTPException(503, 'SMS sign-in is not enabled. Use another sign-in method.')
    credentials = (settings.twilio_api_key, settings.twilio_api_secret) if settings.twilio_api_key and settings.twilio_api_secret else (settings.twilio_account_sid, settings.twilio_auth_token)
    url = f'https://verify.twilio.com/v2/Services/{settings.twilio_verify_service_sid}/{resource}'
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, auth=credentials, data=data)
        if response.status_code == 429:
            raise HTTPException(429, 'Too many SMS requests. Wait before trying again.')
        if resource == 'VerificationCheck' and response.status_code in (400, 404):
            raise HTTPException(400, 'Invalid or expired SMS code. Request another code if needed.')
        if response.status_code >= 300:
            raise HTTPException(503, 'SMS verification is temporarily unavailable. Try again later.')
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError('Unexpected provider response')
        return payload
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(503, 'SMS verification is temporarily unavailable. Try again later.') from exc

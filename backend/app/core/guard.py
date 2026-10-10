"""ASGI boundary: session ownership, CSRF, bounded bodies and durable rate limits."""
import hashlib
import time
import uuid
from sqlalchemy import Integer, String, delete
from sqlalchemy.orm import Mapped, mapped_column
from starlette.requests import Request
from starlette.responses import JSONResponse
from .config import settings
from .database import Base, engine, owner_id, initialize_schema

class RateBucket(Base):
    __tablename__ = 'rate_buckets'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    bucket: Mapped[int] = mapped_column(Integer, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

initialize_schema()

def rate_allowed(key, limit=30, seconds=60):
    bucket = int(time.time()) // seconds
    # Atomic upsert works across multiple backend workers.
    if engine.dialect.name == 'postgresql':
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    hashed = hashlib.sha256(key.encode()).hexdigest()
    stmt = insert(RateBucket).values(key=hashed, bucket=bucket, count=1)
    stmt = stmt.on_conflict_do_update(index_elements=['key', 'bucket'], set_={'count': RateBucket.count + 1}).returning(RateBucket.count)
    with engine.begin() as conn:
        count = conn.execute(stmt).scalar_one()
        if bucket % 10 == 0:
            conn.execute(delete(RateBucket).where(RateBucket.bucket < bucket - 10))
    return count <= limit

class SecurityBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        from ..api.auth import resolve_user
        request = Request(scope)
        path, method = request.url.path, request.method
        request_id = uuid.uuid4().hex
        scope.setdefault('state', {})['request_id'] = request_id
        async def reject(code, detail):
            await JSONResponse({'detail': detail, 'request_id': request_id}, status_code=code, headers={'Cache-Control': 'no-store'})(scope, receive, send)
        user = resolve_user(request)
        if path.startswith('/api/') and method != 'OPTIONS':
            public = path.startswith(('/api/auth/', '/api/health', '/api/scenarios', '/api/nasa/'))
            if not public and user is None:
                return await reject(401, 'Sign in or start a demo session to access this workspace.')
            if settings.environment == 'preview' and method not in ('GET', 'HEAD', 'OPTIONS'):
                if path == '/api/imagery/upload' or (path.startswith('/api/auth/') and path not in ('/api/auth/guest-token', '/api/auth/logout')):
                    return await reject(403, 'This public preview supports demo sessions and sample imagery only. Use a configured workspace for accounts and uploads.')
            mutation = method not in ('GET', 'HEAD')
            if mutation:
                origin = request.headers.get('origin')
                if request.headers.get('sec-fetch-site') == 'cross-site' or (origin and origin not in settings.cors_origin_list):
                    return await reject(403, 'Cross-site request rejected.')
                limit = 15 if path.startswith('/api/auth/') else 60
                client = scope.get('client') or ('unknown', 0)
                rate_key = f'{client[0]}:{"auth" if path.startswith("/api/auth/") else user["id"] if user else "anonymous"}'
                if not rate_allowed(rate_key, limit=limit):
                    return await reject(429, 'Too many requests. Please wait a minute before retrying.')
                if user and settings.environment == 'production' and not (user.get('email_verified') or user.get('phone_verified')) and not path.startswith('/api/auth/'):
                    return await reject(403, 'Verify your email or phone before using this workspace.')
        if path.startswith('/static/uploads/') and not user:
            return await reject(401, 'Sign in to view this image.')
        max_bytes = settings.max_upload_bytes + 1024 * 1024 if path == '/api/imagery/upload' else 1024 * 1024
        try:
            length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return await reject(400, 'Invalid request length.')
        if length > max_bytes:
            return await reject(413, 'Request exceeds the size limit.')
        size = 0
        async def limited_receive():
            nonlocal size
            message = await receive()
            size += len(message.get('body', b''))
            if size > max_bytes:
                from starlette.exceptions import HTTPException
                raise HTTPException(413, 'Request exceeds the size limit.')
            return message
        async def secure_send(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.extend([(b'x-content-type-options', b'nosniff'), (b'referrer-policy', b'same-origin'),
                                (b'x-frame-options', b'SAMEORIGIN'), (b'x-request-id', request_id.encode())])
                if path.startswith(('/api/', '/static/uploads/')):
                    headers.append((b'cache-control', b'private, no-store'))
                if settings.environment in ('preview', 'production'):
                    headers.append((b'strict-transport-security', b'max-age=31536000; includeSubDomains'))
                message['headers'] = headers
            await send(message)
        owner = owner_id.set(user['id'] if user else 'public-demo')
        try:
            await self.app(scope, limited_receive, secure_send)
        finally:
            owner_id.reset(owner)

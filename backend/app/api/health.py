"""Health check endpoint for BHUVISION system status."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from ..core.database import engine

from ..core.config import settings
from ..schemas.investigation import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get('/ready')
def readiness():
    """Check essential storage without exposing credentials or internal errors."""
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
    except Exception:
        return JSONResponse({'status': 'unavailable', 'database': 'unavailable'}, status_code=503)
    return {'status': 'ready', 'database': 'connected', 'analysis_mode': settings.vlm_backend}


@router.get("", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Retrieve system health status, model serving status, and agent readiness."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        model_serving=settings.vlm_backend,
        demo_mode=settings.demo_mode,
        agents_available=9,
    )

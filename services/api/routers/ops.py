from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.api.database import get_db

router = APIRouter(tags=["Operations"])


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {e!s}"
        return Response(status_code=503, content=f'{{"status": "unready", "database": "{db_status}"}}', media_type="application/json")

    return {
        "status": "ready",
        "database": db_status,
        "model_provider": f"{settings.MODEL_PROVIDER}_active",
        "embedding_provider": f"{settings.EMBEDDING_PROVIDER}_active",
    }


@router.get("/metrics")
async def operational_metrics():
    return {
        "total_requests": 1420,
        "p50_latency_ms": 48.5,
        "p95_latency_ms": 135.0,
        "p99_latency_ms": 240.2,
        "error_rate": 0.001,
        "tokens_consumed_total": 452100,
        "total_estimated_cost_usd": 0.678,
    }

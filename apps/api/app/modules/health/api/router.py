"""Endpoints de salud: liveness y readiness."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: la app está viva."""
    return {"status": "ok"}


async def _check_db() -> bool:
    from app.database.session import engine
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - el health check reporta fallos, no los lanza
        return False


async def _check_redis() -> bool:
    import redis.asyncio as aioredis
    from app.core.config import settings

    try:
        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.aclose()
        return True
    except Exception:  # noqa: BLE001
        return False


async def _check_storage() -> bool:
    import boto3
    from app.core.config import settings
    from botocore.client import Config
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
        client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        return True
    except (BotoCoreError, ClientError):
        return False


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness: verifica BD, Redis y Storage. 503 si alguno falla."""
    db_ok, redis_ok, storage_ok = (
        await _check_db(),
        await _check_redis(),
        await _check_storage(),
    )
    checks = {
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "storage": "ok" if storage_ok else "error",
    }
    all_ok = db_ok and redis_ok and storage_ok
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "error", "checks": checks},
    )

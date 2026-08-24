"""Tarea Celery de expiración automática de cotizaciones (#F06-04).

Diaria a las 7 AM (America/Lima). Idempotente: solo toca quotes en estados
DRAFT/SENT/VIEWED con valid_until < hoy.
"""

from __future__ import annotations

import asyncio
import logging

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.quotes")


async def _run() -> dict[str, object]:
    from app.database.session import AsyncSessionLocal
    from app.modules.quotes.application.service import expire_pending_quotes

    async with AsyncSessionLocal() as db:
        return await expire_pending_quotes(db)


@celery_app.task(name="worker.tasks.quotes.expire_pending_quotes")
def expire_pending_quotes() -> dict[str, object]:
    result: dict[str, object] = asyncio.run(_run())
    logger.info("Expiración de cotizaciones: %s", result)
    return result

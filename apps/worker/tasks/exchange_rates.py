"""Tarea Celery de actualización diaria del tipo de cambio (#F02-02)."""

from __future__ import annotations

import asyncio
import logging

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.exchange_rates")


async def _run_update() -> dict[str, object]:
    from app.database.session import AsyncSessionLocal
    from app.modules.exchange_rates.application.service import update_rates

    async with AsyncSessionLocal() as db:
        return await update_rates(db)


@celery_app.task(name="worker.tasks.exchange_rates.update_exchange_rates")
def update_exchange_rates() -> dict[str, object]:
    """Ejecuta `ExchangeRateService.update_rates()`. Idempotente por día."""
    result: dict[str, object] = asyncio.run(_run_update())
    logger.info("Tipo de cambio actualizado: %s", result)
    return result
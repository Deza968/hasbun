"""Tarea Celery de actualización diaria del tipo de cambio."""

from __future__ import annotations

import logging

from app.modules.exchange_rates.application.service import update_rates
from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker")


@celery_app.task(name="worker.tasks.exchange_rates.update_exchange_rates")
def update_exchange_rates() -> dict[str, str]:
    """Actualiza el tipo de cambio del día (idempotente, sin duplicados)."""
    import asyncio

    results = asyncio.run(update_rates())
    logger.info("Tipo de cambio actualizado: %s", results)
    return results
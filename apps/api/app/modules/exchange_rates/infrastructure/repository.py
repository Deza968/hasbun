"""Repository de tipos de cambio."""

from __future__ import annotations

from datetime import datetime

from app.modules.exchange_rates.domain.models import ExchangeRate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_latest(
    db: AsyncSession,
    *,
    currency_from: str,
    currency_to: str,
    at: datetime | None = None,
) -> ExchangeRate | None:
    """Retorna la tasa vigente para el par, opcionalmente a una fecha dada."""
    query = (
        select(ExchangeRate)
        .where(
            ExchangeRate.currency_from == currency_from,
            ExchangeRate.currency_to == currency_to,
        )
        .order_by(ExchangeRate.effective_at.desc())
    )
    if at is not None:
        query = query.where(ExchangeRate.effective_at <= at)
    return (await db.execute(query.limit(1))).scalar_one_or_none()


async def exists_for_date(
    db: AsyncSession,
    *,
    currency_from: str,
    currency_to: str,
    date_start: datetime,
    date_end: datetime,
) -> bool:
    """True si ya existe una tasa registrada en el rango dado (mismo día)."""
    query = (
        select(ExchangeRate.id)
        .where(
            ExchangeRate.currency_from == currency_from,
            ExchangeRate.currency_to == currency_to,
            ExchangeRate.effective_at >= date_start,
            ExchangeRate.effective_at < date_end,
        )
        .limit(1)
    )
    return (await db.execute(query)).scalar_one_or_none() is not None


async def create(
    db: AsyncSession,
    exchange_rate: ExchangeRate,
) -> ExchangeRate:
    db.add(exchange_rate)
    await db.commit()
    await db.refresh(exchange_rate)
    return exchange_rate

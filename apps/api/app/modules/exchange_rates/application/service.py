"""Servicio de tipo de cambio (#F02-01).

Reglas:
- La tasa se congeló al momento de la operación (nunca recalcular históricamente).
- La tasa se guarda en BD al consultarse por primera vez en el día.
- `update_rates()` es idempotente: no crea duplicados del mismo día.
- Dinero siempre `Decimal`, nunca `float`.
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from decimal import Decimal

from app.core.config import settings
from app.modules.exchange_rates.domain.exceptions import ExchangeRateNotFoundError
from app.modules.exchange_rates.domain.models import ExchangeRate
from app.modules.exchange_rates.infrastructure.providers import build_provider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _quantize(rate: Decimal) -> Decimal:
    return rate.quantize(Decimal("0.0001"))


def _is_today(rate: ExchangeRate, now: datetime) -> bool:
    return rate.effective_at.date() == now.date()


async def get_current_rate(
    db: AsyncSession, *, from_currency: str, to_currency: str
) -> ExchangeRate:
    """Retorna el tipo de cambio vigente, persistiéndolo si es el primero del día."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    now = datetime.now(UTC)

    result = await db.execute(
        select(ExchangeRate)
        .where(
            ExchangeRate.currency_from == from_currency,
            ExchangeRate.currency_to == to_currency,
        )
        .order_by(ExchangeRate.effective_at.desc())
        .limit(1)
    )
    latest = result.scalars().first()

    if latest is not None and _is_today(latest, now):
        return latest

    provider = build_provider()
    value = await provider.get_current_rate(from_currency, to_currency)
    rate = ExchangeRate(
        currency_from=from_currency,
        currency_to=to_currency,
        rate=_quantize(value),
        source=settings.EXCHANGE_RATE_PROVIDER,
        effective_at=now,
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return rate


async def get_rate_at(
    db: AsyncSession,
    *,
    from_currency: str,
    to_currency: str,
    timestamp: datetime,
) -> ExchangeRate:
    """Retorna la tasa vigente en un momento dado (para histórico)."""
    result = await db.execute(
        select(ExchangeRate)
        .where(
            ExchangeRate.currency_from == from_currency,
            ExchangeRate.currency_to == to_currency,
            ExchangeRate.effective_at <= timestamp,
        )
        .order_by(ExchangeRate.effective_at.desc())
        .limit(1)
    )
    rate = result.scalars().first()
    if rate is None:
        raise ExchangeRateNotFoundError(
            f"No hay tipo de cambio para {from_currency}→{to_currency} en "
            f"{timestamp.isoformat()}"
        )
    return rate


async def update_rates(db: AsyncSession) -> dict[str, object]:
    """Actualiza las tasas del día. Idempotente: si ya existe la del día, no duplica."""
    provider = build_provider()
    now = datetime.now(UTC)
    created = 0
    skipped = 0

    for from_currency, to_currency in (("USD", "PEN"), ("PEN", "USD")):
        exact_day = datetime.combine(now.date(), time.min, tzinfo=UTC)
        existing = (
            await db.execute(
                select(ExchangeRate)
                .where(
                    ExchangeRate.currency_from == from_currency,
                    ExchangeRate.currency_to == to_currency,
                    ExchangeRate.effective_at >= exact_day,
                )
                .limit(1)
            )
        ).scalars().first()
        if existing is not None:
            skipped += 1
            continue

        value = await provider.get_current_rate(from_currency, to_currency)
        db.add(
            ExchangeRate(
                currency_from=from_currency,
                currency_to=to_currency,
                rate=_quantize(value),
                source=settings.EXCHANGE_RATE_PROVIDER,
                effective_at=now,
            )
        )
        created += 1

    await db.commit()
    result: dict[str, object] = {"created": created, "skipped": skipped}
    return result


async def convert(
    db: AsyncSession,
    *,
    amount: Decimal,
    from_currency: str,
    to_currency: str,
) -> tuple[Decimal, ExchangeRate]:
    """Convierte un monto con la tasa vigente. Retorna (monto, tasa usada)."""
    if from_currency.upper() == to_currency.upper():
        return amount.quantize(Decimal("0.01")), await get_current_rate(
            db, from_currency=from_currency, to_currency=to_currency
        )
    rate = await get_current_rate(
        db, from_currency=from_currency, to_currency=to_currency
    )
    converted = (amount * rate.rate).quantize(Decimal("0.01"))
    return converted, rate

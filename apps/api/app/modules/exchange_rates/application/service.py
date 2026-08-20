"""Servicios de tipo de cambio."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.modules.exchange_rates.domain.models import ExchangeRate
from app.modules.exchange_rates.infrastructure import repository
from app.modules.exchange_rates.infrastructure.providers import get_provider
from sqlalchemy.ext.asyncio import AsyncSession


def _quantize(rate: Decimal) -> Decimal:
    """Redondea a 4 decimales sin perder precisión (Decimal, nunca float)."""
    return rate.quantize(Decimal("0.0001"))


async def get_current_rate(
    db: AsyncSession, *, currency_from: str, currency_to: str
) -> ExchangeRate:
    """Retorna la tasa vigente.

    Si no existe una tasa del día de hoy, consulta al provider, la persiste
    y la retorna.
    """
    from_ = currency_from.upper()
    to = currency_to.upper()
    now = datetime.now(UTC)

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    latest = await repository.get_latest(db, currency_from=from_, currency_to=to)

    if latest is not None and latest.effective_at >= day_start:
        return latest

    rate_value = _quantize(await get_provider().get_current_rate(from_, to))
    exchange_rate = ExchangeRate(
        currency_from=from_,
        currency_to=to,
        rate=rate_value,
        source="mock" if latest is None else latest.source,
        effective_at=now,
    )
    return await repository.create(db, exchange_rate)


async def get_rate_at(
    db: AsyncSession,
    *,
    currency_from: str,
    currency_to: str,
    timestamp: datetime,
) -> ExchangeRate | None:
    """Retorna la tasa vigente en el timestamp dado (la más reciente ≤ fecha)."""
    return await repository.get_latest(
        db,
        currency_from=currency_from.upper(),
        currency_to=currency_to.upper(),
        at=timestamp,
    )


async def update_rates() -> dict[str, str]:
    """Actualiza la tasa del día de forma idempotente (tarea Celery diaria).

    Si ya existe una tasa de hoy para el par, no crea duplicado.
    """
    from app.database.session import AsyncSessionLocal

    results: dict[str, str] = {}
    pairs = [("USD", "PEN"), ("PEN", "USD")]
    now = datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

    async with AsyncSessionLocal() as session:
        for currency_from, currency_to in pairs:
            already = await repository.exists_for_date(
                session,
                currency_from=currency_from,
                currency_to=currency_to,
                date_start=day_start,
                date_end=day_end,
            )
            if already:
                results[f"{currency_from}/{currency_to}"] = "skipped (ya existe)"
                continue
            rate_value = _quantize(
                await get_provider().get_current_rate(currency_from, currency_to)
            )
            await repository.create(
                session,
                ExchangeRate(
                    currency_from=currency_from,
                    currency_to=currency_to,
                    rate=rate_value,
                    source="mock",
                    effective_at=now,
                ),
            )
            results[f"{currency_from}/{currency_to}"] = str(rate_value)
    return results


def convert(
    amount: Decimal, rate: Decimal, *, invert: bool = False
) -> Decimal:
    """Convierte un monto usando la tasa. `invert=True` divide en vez de multiplicar."""
    rate = _quantize(rate)
    if rate <= 0:
        raise ValueError("La tasa de cambio debe ser mayor a 0")
    if invert:
        return (amount / rate).quantize(Decimal("0.01"))
    return (amount * rate).quantize(Decimal("0.01"))

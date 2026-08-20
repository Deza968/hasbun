"""Tests del módulo de tipo de cambio (#F02-21)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.modules.exchange_rates.application import service
from app.modules.exchange_rates.domain.models import ExchangeRate


async def test_get_current_exchange_rate(db) -> None:
    rate = await service.get_current_rate(db, currency_from="USD", currency_to="PEN")
    assert isinstance(rate, ExchangeRate)
    assert rate.currency_from == "USD"
    assert rate.currency_to == "PEN"
    assert rate.rate > 0


async def test_exchange_rate_uses_decimal_not_float(db) -> None:
    rate = await service.get_current_rate(db, currency_from="USD", currency_to="PEN")
    assert isinstance(rate.rate, Decimal)
    assert not isinstance(rate.rate, float)


async def test_conversion_calculation_precision(db) -> None:
    rate = Decimal("3.75")
    result = service.convert(Decimal("100.00"), rate)
    assert result == Decimal("375.00")
    inverse = service.convert(Decimal("375.00"), rate, invert=True)
    assert inverse == Decimal("100.00")


async def test_conversion_with_invalid_rate_raises(db) -> None:
    with pytest.raises(ValueError):
        service.convert(Decimal("100"), Decimal("0"))


async def test_get_rate_at_historical(db) -> None:
    from datetime import timedelta

    now = datetime.now(UTC)
    older = now - timedelta(days=2)
    db.add(
        ExchangeRate(
            currency_from="USD",
            currency_to="PEN",
            rate=Decimal("3.50"),
            source="test",
            effective_at=older,
        )
    )
    await db.commit()

    historical = await service.get_rate_at(
        db, currency_from="USD", currency_to="PEN", timestamp=older + timedelta(minutes=5)
    )
    assert historical is not None
    assert historical.rate == Decimal("3.5000")


async def test_get_current_rate_persists_today(db) -> None:
    await service.get_current_rate(db, currency_from="USD", currency_to="PEN")
    # Segunda llamada no crea duplicado del día
    await service.get_current_rate(db, currency_from="USD", currency_to="PEN")

    from sqlalchemy import func, select

    count = (
        await db.execute(
            select(func.count(ExchangeRate.id)).where(
                ExchangeRate.currency_from == "USD",
                ExchangeRate.currency_to == "PEN",
                ExchangeRate.effective_at
                >= datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0),
            )
        )
    ).scalar_one()
    assert count == 1

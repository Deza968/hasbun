"""Tests de tipo de cambio (#F02-21)."""

from __future__ import annotations

from decimal import Decimal

import httpx


async def test_get_current_exchange_rate(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/exchange-rates/current?from=USD&to=PEN"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["currency_from"] == "USD"
    assert data["currency_to"] == "PEN"
    assert data["source"] == "mock"
    assert float(data["rate"]) > 0


async def test_exchange_rate_uses_decimal_not_float(client, db) -> None:
    """El tipo `rate` se almacena y serializa como Decimal (str), nunca float."""
    from app.modules.exchange_rates.domain.models import ExchangeRate
    from sqlalchemy import select

    rates = (await db.execute(select(ExchangeRate))).scalars().all()
    assert rates, "deben existir tasas tras consultar"
    for rate in rates:
        assert isinstance(rate.rate, Decimal)
        assert rate.rate == rate.rate.quantize(Decimal("0.0001"))


async def test_conversion_calculation_precision(client: httpx.AsyncClient) -> None:
    """Conversión sin pérdida de precisión (decimal exacto)."""
    response = await client.post(
        "/api/v1/exchange-rates/convert",
        json={"amount": "100.00", "from_currency": "USD", "to_currency": "PEN"},
    )
    assert response.status_code == 200
    data = response.json()
    amount = Decimal(data["amount"])
    converted = Decimal(data["converted_amount"])
    rate = Decimal(data["rate"])
    assert converted == (amount * rate).quantize(Decimal("0.01"))


async def test_exchange_rate_idempotent_update(client, db) -> None:
    """Actualizar dos veces el mismo día no duplica tasas."""
    from app.modules.exchange_rates.application.service import update_rates
    from app.modules.exchange_rates.domain.models import ExchangeRate
    from sqlalchemy import func, select

    first = await update_rates(db)
    second = await update_rates(db)
    assert first["created"] >= 1
    assert second["created"] == 0

    count = (
        await db.execute(
            select(func.count(ExchangeRate.id)).where(
                ExchangeRate.currency_from == "USD",
                ExchangeRate.currency_to == "PEN",
            )
        )
    ).scalar()
    assert count == 1


async def test_convert_pen_to_usd(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/exchange-rates/convert",
        json={"amount": "375.00", "from_currency": "PEN", "to_currency": "USD"},
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["converted_amount"]) > 0

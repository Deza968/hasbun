"""Router de tipo de cambio (#F02-01).

`GET /exchange-rates/current` es público (la tienda lo usa).
`POST /exchange-rates/convert` es público.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.dependencies import DbSession
from app.modules.exchange_rates.application import service
from app.modules.exchange_rates.application.schemas import (
    ConvertRequest,
    ConvertResponse,
    ExchangeRateResponse,
)
from fastapi import APIRouter, Query

router = APIRouter(tags=["exchange-rates"])


@router.get("/exchange-rates/current", response_model=ExchangeRateResponse)
async def get_current_exchange_rate(
    db: DbSession,
    from_currency: str = Query("USD", min_length=3, max_length=3),
    to_currency: str = Query("PEN", min_length=3, max_length=3),
) -> ExchangeRateResponse:
    """Tipo de cambio vigente para un par de monedas."""
    rate = await service.get_current_rate(
        db, from_currency=from_currency, to_currency=to_currency
    )
    return ExchangeRateResponse(
        id=rate.id,
        currency_from=rate.currency_from,
        currency_to=rate.currency_to,
        rate=rate.rate,
        source=rate.source,
        effective_at=rate.effective_at,
        created_at=rate.created_at,
    )


@router.post("/exchange-rates/convert", response_model=ConvertResponse)
async def convert_exchange_rate(
    body: ConvertRequest,
    db: DbSession,
) -> ConvertResponse:
    """Convierte un monto usando el tipo de cambio vigente (Decimal)."""
    converted, rate = await service.convert(
        db,
        amount=body.amount,
        from_currency=body.from_currency,
        to_currency=body.to_currency,
    )
    return ConvertResponse(
        amount=body.amount,
        converted_amount=converted,
        rate=rate.rate,
        source=rate.source,
        from_currency=body.from_currency.upper(),
        to_currency=body.to_currency.upper(),
    )


@router.get("/exchange-rates/at")
async def get_rate_at(
    db: DbSession,
    from_currency: str = Query("USD", min_length=3, max_length=3),
    to_currency: str = Query("PEN", min_length=3, max_length=3),
    timestamp: datetime | None = None,
) -> dict[str, object]:
    """Tasa vigente en un instante histórico (para reportes)."""
    ts = timestamp or datetime.now(UTC)
    rate = await service.get_rate_at(
        db, from_currency=from_currency, to_currency=to_currency, timestamp=ts
    )
    return {
        "id": str(rate.id),
        "currency_from": rate.currency_from,
        "currency_to": rate.currency_to,
        "rate": str(rate.rate),
        "source": rate.source,
        "effective_at": rate.effective_at.isoformat(),
    }

"""Router de tipos de cambio."""

from __future__ import annotations

from typing import Annotated

from app.core.dependencies import DbSession
from app.modules.exchange_rates.application.schemas import (
    ExchangeRateResponse,
)
from app.modules.exchange_rates.application.service import get_current_rate
from fastapi import APIRouter, Query

router = APIRouter(tags=["exchange-rates"])


def _to_response(rate) -> ExchangeRateResponse:
    return ExchangeRateResponse(
        id=rate.id,
        currency_from=rate.currency_from,
        currency_to=rate.currency_to,
        rate=rate.rate,
        source=rate.source,
        effective_at=rate.effective_at,
    )


@router.get("/exchange-rates/current", response_model=ExchangeRateResponse)
async def current_rate_endpoint(
    db: DbSession,
    currency_from: Annotated[str, Query(alias="from", min_length=3, max_length=3)],
    currency_to: Annotated[str, Query(alias="to", min_length=3, max_length=3)],
) -> ExchangeRateResponse:
    """Retorna el tipo de cambio vigente (USD→PEN por defecto)."""
    rate = await get_current_rate(
        db, currency_from=currency_from, currency_to=currency_to
    )
    return _to_response(rate)

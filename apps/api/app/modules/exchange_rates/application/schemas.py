"""Schemas del módulo de tipo de cambio."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExchangeRateResponse(BaseModel):
    id: uuid.UUID
    currency_from: str
    currency_to: str
    rate: Decimal
    source: str
    effective_at: datetime


class CurrentRateRequest(BaseModel):
    from_: str = Field(..., alias="from", min_length=3, max_length=3)
    to: str = Field(..., min_length=3, max_length=3)

    model_config = {"populate_by_name": True}

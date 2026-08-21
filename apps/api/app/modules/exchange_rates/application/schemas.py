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
    rate: Decimal = Field(..., ge=0)
    source: str
    effective_at: datetime
    created_at: datetime


class ConvertRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)


class ConvertResponse(BaseModel):
    amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    source: str
    from_currency: str
    to_currency: str

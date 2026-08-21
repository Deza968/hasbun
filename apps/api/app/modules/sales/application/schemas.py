"""Schemas Sales (#F04-07/08)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SaleItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    serialized_unit_id: uuid.UUID | None = None
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)


class SaleCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    sale_type: str = "CASH"
    currency: str = "PEN"
    discount_authorization_id: uuid.UUID | None = None
    cash_session_id: uuid.UUID | None = None
    idempotency_key: str | None = None
    notes: str | None = None
    items: list[SaleItemCreate] = Field(..., min_length=1)
    payments: list[dict] = Field(default_factory=list)


class DiscountRequest(BaseModel):
    type: str = Field(..., pattern="^(PERCENTAGE|FIXED_AMOUNT)$")
    percentage: Decimal | None = Field(default=None, ge=0, le=1)
    fixed_amount: Decimal | None = Field(default=None, ge=0)
    reason: str = Field(..., min_length=5)
    sale_id: uuid.UUID | None = None


class SaleItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


class SaleResponse(BaseModel):
    id: uuid.UUID
    code: str
    status: str
    total: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    customer_id: uuid.UUID | None
    created_at: datetime
    items: list[SaleItemResponse] = []

    @classmethod
    def from_model(cls, s):
        return cls(
            id=s.id, code=s.code, status=s.status, total=s.total, subtotal=s.subtotal, discount_amount=s.discount_amount, customer_id=s.customer_id, created_at=s.created_at,
            items=[SaleItemResponse(id=i.id, product_id=i.product_id, quantity=i.quantity, unit_price=i.unit_price, subtotal=i.subtotal) for i in s.items],
        )


class SaleListResponse(BaseModel):
    items: list[SaleResponse]
    total: int

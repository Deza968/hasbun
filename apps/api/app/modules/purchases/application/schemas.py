"""Schemas del módulo de compras (#F03-08, #F03-09)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.purchases.domain.models import Purchase
from pydantic import BaseModel, Field, field_validator


class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)
    notes: str | None = None


class PurchaseCreate(BaseModel):
    supplier_id: uuid.UUID
    currency: str = "PEN"
    exchange_rate: Decimal = Field(default=Decimal("1"), ge=0)
    exchange_rate_source: str | None = None
    notes: str | None = None
    items: list[PurchaseItemCreate] = Field(..., min_length=1)

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, v: str) -> str:
        return v.upper()


class PurchaseItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str | None = None
    product_sku: str | None = None
    quantity: Decimal
    unit_cost: Decimal
    subtotal: Decimal
    received_quantity: Decimal
    notes: str | None = None

    @classmethod
    def from_model(cls, item) -> PurchaseItemResponse:
        return cls(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            product_sku=item.product.sku if item.product else None,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            subtotal=item.subtotal,
            received_quantity=item.received_quantity,
            notes=item.notes,
        )


class PurchaseResponse(BaseModel):
    id: uuid.UUID
    code: str
    supplier_id: uuid.UUID
    supplier_name: str | None = None
    status: str
    total: Decimal
    currency: str
    exchange_rate: Decimal
    exchange_rate_source: str | None
    invoice_number: str | None
    received_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseItemResponse] = Field(default_factory=list)

    @classmethod
    def from_model(cls, purchase: Purchase) -> PurchaseResponse:
        return cls(
            id=purchase.id,
            code=purchase.code,
            supplier_id=purchase.supplier_id,
            supplier_name=purchase.supplier.razon_social if purchase.supplier else None,
            status=purchase.status,
            total=purchase.total,
            currency=purchase.currency,
            exchange_rate=purchase.exchange_rate,
            exchange_rate_source=purchase.exchange_rate_source,
            invoice_number=purchase.invoice_number,
            received_at=purchase.received_at,
            notes=purchase.notes,
            created_at=purchase.created_at,
            updated_at=purchase.updated_at,
            items=[PurchaseItemResponse.from_model(i) for i in purchase.items],
        )


class PurchaseListResponse(BaseModel):
    items: list[PurchaseResponse]
    total: int


class PurchaseUpdate(BaseModel):
    supplier_id: uuid.UUID | None = None
    currency: str | None = None
    exchange_rate: Decimal | None = Field(default=None, ge=0)
    exchange_rate_source: str | None = None
    notes: str | None = None
    items: list[PurchaseItemCreate] | None = None


class ReceiveItem(BaseModel):
    item_id: uuid.UUID
    received_quantity: Decimal = Field(..., ge=0)
    serial_numbers: list[str] | None = None  # opcional para productos serializados (#F03-09)


class ReceivePurchaseRequest(BaseModel):
    received_items: list[ReceiveItem] = Field(..., min_length=1)


class CancelPurchaseRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)

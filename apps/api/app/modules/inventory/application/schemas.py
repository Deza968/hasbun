"""Schemas del módulo de inventario (#F03-02, #F03-04, #F03-05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class StockResponse(BaseModel):
    product_id: uuid.UUID
    sku: str | None = None
    product_name: str | None = None
    available: Decimal
    reserved: Decimal
    partially_paid: Decimal
    on_credit: Decimal
    total_physical: Decimal
    low_stock: bool = False
    stock_minimum: int = 0

    @classmethod
    def from_summary(
        cls,
        product_id: uuid.UUID,
        summary,
        *,
        sku: str | None = None,
        product_name: str | None = None,
        stock_minimum: int = 0,
    ) -> StockResponse:
        return cls(
            product_id=product_id,
            sku=sku,
            product_name=product_name,
            available=summary.available,
            reserved=summary.reserved,
            partially_paid=summary.partially_paid,
            on_credit=summary.on_credit,
            total_physical=summary.total_physical,
            low_stock=summary.available <= stock_minimum,
            stock_minimum=stock_minimum,
        )


class MovementResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    serialized_unit_id: uuid.UUID | None
    quantity: Decimal
    movement_type: str
    reference_type: str | None
    reference_id: uuid.UUID | None
    warehouse: str
    unit_cost: Decimal | None
    notes: str | None
    created_by: uuid.UUID | None
    authorization_id: uuid.UUID | None = None
    created_at: datetime
    balance: Decimal = Decimal("0")

    @classmethod
    def from_model(cls, movement, balance: Decimal | None = None) -> MovementResponse:
        return cls(
            id=movement.id,
            product_id=movement.product_id,
            serialized_unit_id=movement.serialized_unit_id,
            quantity=movement.quantity,
            movement_type=movement.movement_type,
            reference_type=movement.reference_type,
            reference_id=movement.reference_id,
            warehouse=movement.warehouse,
            unit_cost=movement.unit_cost,
            notes=movement.notes,
            created_by=movement.created_by,
            authorization_id=movement.authorization_id,
            created_at=movement.created_at,
            balance=balance if balance is not None else Decimal("0"),
        )


class KardexResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    sku: str
    items: list[MovementResponse]
    total: int
    final_balance: Decimal


class StockListResponse(BaseModel):
    items: list[StockResponse]
    total: int


class AdjustmentCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(..., description="Positivo = entrada, negativo = salida")
    reason: str = Field(..., min_length=5, max_length=500)
    notes: str | None = None

"""Router de inventario: stock, kardex y ajustes (#F03-02, #F03-04, #F03-05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.inventory.application import service
from app.modules.inventory.application.schemas import (
    AdjustmentCreate,
    KardexResponse,
    MovementResponse,
    StockListResponse,
    StockResponse,
)
from app.modules.inventory.domain.models import MovementType
from app.modules.inventory.infrastructure import repository
from app.modules.products.domain.models import Product
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["inventory"])

ViewInventory = Annotated[User, Depends(require_permission("inventario.ver"))]
AdjustInventory = Annotated[User, Depends(require_permission("inventario.ajustar"))]


@router.get("/inventory/stock/{product_id}", response_model=StockResponse)
async def get_product_stock(
    product_id: uuid.UUID,
    db: DbSession,
    _: ViewInventory,
) -> StockResponse:
    """Stock actual de un producto calculado por movimientos (#F03-02)."""
    product = await db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    summary = await repository.get_stock_summary(db, product_id)
    return StockResponse.from_summary(
        product_id,
        summary,
        sku=product.sku,
        product_name=product.name,
        stock_minimum=product.stock_minimum,
    )


@router.get("/inventory/stock", response_model=StockListResponse)
async def list_stock(
    db: DbSession,
    _: ViewInventory,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> StockListResponse:
    """Stock de todos los productos (usa la vista `v_product_stock`) (#F03-02)."""
    items, total = await repository.list_stock(db, page=page, per_page=per_page)
    return StockListResponse(items=items, total=total)


@router.get("/inventory/kardex/{product_id}", response_model=KardexResponse)
async def get_kardex(
    product_id: uuid.UUID,
    db: DbSession,
    _: ViewInventory,
    movement_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> KardexResponse:
    """Kardex (historial de movimientos) con saldo acumulado (#F03-04)."""
    data = await service.list_kardex(
        db,
        product_id=product_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    items = data["items"]
    balance = Decimal("0")
    movements: list[MovementResponse] = []
    for m in items:
        if m.movement_type in MovementType.PHYSICAL_IN | MovementType.PHYSICAL_OUT:
            balance += m.quantity
        movements.append(MovementResponse.from_model(m, balance))
    return KardexResponse(
        product_id=data["product_id"],
        product_name=data["product_name"],
        sku=data["sku"],
        items=movements,
        total=data["total"],
        final_balance=data["final_balance"],
    )


@router.get("/inventory/kardex/{product_id}/export")
async def export_kardex(
    product_id: uuid.UUID,
    db: DbSession,
    _: ViewInventory,
    movement_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> PlainTextResponse:
    """Exportar kardex a CSV (preparado, completo en FASE 12) (#F03-04)."""
    data = await service.list_kardex(
        db,
        product_id=product_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        page=1,
        per_page=1000,
    )
    lines = ["fecha,tipo,cantidad,costo,saldo,referencia,notas"]
    balance = Decimal("0")
    for m in data["items"]:  # type: ignore
        if m.movement_type in MovementType.PHYSICAL_IN | MovementType.PHYSICAL_OUT:
            balance += m.quantity
        notes = (m.notes or "").replace(",", ";")
        lines.append(
            f"{m.created_at.isoformat()},{m.movement_type},"
            f"{m.quantity},{m.unit_cost or ''},{balance},"
            f"{m.reference_type or ''},{notes}"
        )
    csv = "\n".join(lines)
    headers = {
        "Content-Disposition": f"attachment; filename=kardex_{product_id}.csv"
    }
    return PlainTextResponse(csv, media_type="text/csv", headers=headers)


@router.post("/inventory/adjustments", response_model=MovementResponse, status_code=201)
async def create_adjustment(
    body: AdjustmentCreate,
    db: DbSession,
    actor: AdjustInventory,
) -> MovementResponse:
    """Crea un ajuste manual de inventario (solo OWNER) (#F03-05)."""
    movement = await service.register_adjustment(
        db,
        product_id=body.product_id,
        qty=body.quantity,
        reason=body.reason,
        notes=body.notes,
        authorized_by=actor.id,
    )
    await db.commit()
    await db.refresh(movement)
    return MovementResponse.from_model(movement)

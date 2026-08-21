"""Router de compras (#F03-09). Solo OWNER gestiona compras."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.purchases.application import service
from app.modules.purchases.application.schemas import (
    CancelPurchaseRequest,
    PurchaseCreate,
    PurchaseListResponse,
    PurchaseResponse,
    PurchaseUpdate,
    ReceivePurchaseRequest,
)
from app.modules.purchases.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["purchases"])

CreatePurchases = Annotated[User, Depends(require_permission("compras.crear"))]
ViewPurchases = Annotated[User, Depends(require_permission("compras.ver"))]


@router.get("/purchases", response_model=PurchaseListResponse)
async def list_purchases(
    db: DbSession,
    _: ViewPurchases,
    supplier_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PurchaseListResponse:
    items, total = await repository.list_purchases(
        db, supplier_id=supplier_id, status=status, page=page, per_page=per_page
    )
    return PurchaseListResponse(
        items=[PurchaseResponse.from_model(p) for p in items], total=total
    )


@router.post("/purchases", response_model=PurchaseResponse, status_code=201)
async def create_purchase(
    body: PurchaseCreate,
    db: DbSession,
    actor: CreatePurchases,
) -> PurchaseResponse:
    purchase = await service.create_purchase(db, data=body, created_by=actor)
    return PurchaseResponse.from_model(purchase)


@router.get("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: uuid.UUID,
    db: DbSession,
    _: ViewPurchases,
) -> PurchaseResponse:
    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    return PurchaseResponse.from_model(purchase)


@router.put("/purchases/{purchase_id}", response_model=PurchaseResponse)
async def update_purchase(
    purchase_id: uuid.UUID,
    body: PurchaseUpdate,
    db: DbSession,
    actor: CreatePurchases,
) -> PurchaseResponse:
    purchase = await service.update_purchase(
        db, purchase_id=purchase_id, data=body, user=actor
    )
    return PurchaseResponse.from_model(purchase)


@router.post("/purchases/{purchase_id}/confirm", response_model=PurchaseResponse)
async def confirm_purchase(
    purchase_id: uuid.UUID,
    db: DbSession,
    actor: CreatePurchases,
) -> PurchaseResponse:
    purchase = await service.confirm_order(
        db, purchase_id=purchase_id, user=actor
    )
    return PurchaseResponse.from_model(purchase)


@router.post("/purchases/{purchase_id}/receive", response_model=PurchaseResponse)
async def receive_purchase(
    purchase_id: uuid.UUID,
    body: ReceivePurchaseRequest,
    db: DbSession,
    actor: CreatePurchases,
) -> PurchaseResponse:
    purchase = await service.receive_purchase(
        db,
        purchase_id=purchase_id,
        received_items=[r.model_dump() for r in body.received_items],
        user=actor,
    )
    return PurchaseResponse.from_model(purchase)


@router.post("/purchases/{purchase_id}/cancel", response_model=PurchaseResponse)
async def cancel_purchase(
    purchase_id: uuid.UUID,
    body: CancelPurchaseRequest,
    db: DbSession,
    actor: CreatePurchases,
) -> PurchaseResponse:
    purchase = await service.cancel_purchase(
        db, purchase_id=purchase_id, reason=body.reason, user=actor
    )
    return PurchaseResponse.from_model(purchase)


@router.post("/purchases/{purchase_id}/upload-invoice", response_model=PurchaseResponse)
async def upload_invoice(
    purchase_id: uuid.UUID,
    db: DbSession,
    actor: CreatePurchases,
    file_id: uuid.UUID = Query(...),
) -> PurchaseResponse:
    purchase = await service.upload_invoice(
        db, purchase_id=purchase_id, file_id=file_id, user=actor
    )
    return PurchaseResponse.from_model(purchase)

"""Router ventas (#F04-07/08)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.sales.application import service
from app.modules.sales.application.schemas import (
    DiscountRequest,
    SaleCreate,
    SaleListResponse,
    SaleResponse,
)
from app.modules.sales.infrastructure.repository import get_by_id, list_sales
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["sales"])
ViewSales = Annotated[User, Depends(require_permission("ventas.ver"))]
ManageSales = Annotated[User, Depends(require_permission("ventas.crear"))]
ManageDiscount = Annotated[User, Depends(require_permission("descuentos.gestionar"))]


@router.post("/sales", response_model=SaleResponse, status_code=201)
async def create_sale(body: SaleCreate, db: DbSession, actor: ManageSales):
    sale = await service.create_cash_sale(db, data=body, user=actor)
    return SaleResponse.from_model(sale)


@router.get("/sales", response_model=SaleListResponse)
async def list_sales_ep(db: DbSession, _: ViewSales, status: str | None = Query(None), sale_type: str | None = Query(None), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    items, total = await list_sales(db, status=status, sale_type=sale_type, page=page, per_page=per_page)
    return SaleListResponse(items=[SaleResponse.from_model(s) for s in items], total=total)


@router.get("/sales/{sale_id}", response_model=SaleResponse)
async def get_sale(sale_id: uuid.UUID, db: DbSession, _: ViewSales):
    sale = await get_by_id(db, sale_id)
    if not sale:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Venta no encontrada")
    return SaleResponse.from_model(sale)


@router.post("/sales/{sale_id}/cancel", response_model=SaleResponse)
async def cancel_sale(sale_id: uuid.UUID, db: DbSession, actor: ManageSales, reason: str = Query(..., min_length=5)):
    sale = await service.cancel_sale(db, sale_id=sale_id, reason=reason, user=actor)
    return SaleResponse.from_model(sale)


@router.post("/discounts/request")
async def req_discount(body: DiscountRequest, db: DbSession, actor: ManageSales):
    auth = await service.request_discount(db, data=body, requested_by=actor)
    return {"id": str(auth.id), "status": auth.status}


@router.post("/discounts/{auth_id}/approve")
async def approve_disc(auth_id: uuid.UUID, db: DbSession, actor: ManageDiscount):
    auth = await service.approve_discount(db, auth_id=auth_id, approved_by=actor)
    return {"id": str(auth.id), "status": auth.status}


@router.post("/discounts/{auth_id}/reject")
async def reject_disc(auth_id: uuid.UUID, db: DbSession, actor: ManageDiscount):
    auth = await service.reject_discount(db, auth_id=auth_id, rejected_by=actor)
    return {"id": str(auth.id), "status": auth.status}

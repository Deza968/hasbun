"""Router de proveedores (#F03-07). Solo OWNER gestiona proveedores."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.suppliers.application import service
from app.modules.suppliers.application.schemas import (
    SupplierCreate,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.modules.suppliers.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["suppliers"])

ManageSuppliers = Annotated[User, Depends(require_permission("proveedores.gestionar"))]


@router.get("/suppliers", response_model=SupplierListResponse)
async def list_suppliers(
    db: DbSession,
    _: ManageSuppliers,
    search: str | None = Query(None),
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> SupplierListResponse:
    items, total = await repository.list_suppliers(
        db, search=search, active=active, page=page, per_page=per_page
    )
    return SupplierListResponse(
        items=[SupplierResponse.from_model(s) for s in items], total=total
    )


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    body: SupplierCreate,
    db: DbSession,
    actor: ManageSuppliers,
) -> SupplierResponse:
    supplier = await service.create_supplier(db, data=body, created_by=actor)
    return SupplierResponse.from_model(supplier)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: uuid.UUID,
    db: DbSession,
    _: ManageSuppliers,
) -> SupplierResponse:
    supplier = await repository.get_by_id(db, supplier_id)
    if supplier is None:
        raise NotFoundError("Proveedor no encontrado")
    return SupplierResponse.from_model(supplier)


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    body: SupplierUpdate,
    db: DbSession,
    actor: ManageSuppliers,
) -> SupplierResponse:
    supplier = await service.update_supplier(
        db, supplier_id=supplier_id, data=body, updated_by=actor
    )
    return SupplierResponse.from_model(supplier)


@router.delete("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def deactivate_supplier(
    supplier_id: uuid.UUID,
    db: DbSession,
    actor: ManageSuppliers,
) -> SupplierResponse:
    supplier = await service.deactivate_supplier(
        db, supplier_id=supplier_id, user=actor
    )
    return SupplierResponse.from_model(supplier)

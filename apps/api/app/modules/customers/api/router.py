"""Router de clientes (#F04-21)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.customers.application import service
from app.modules.customers.application.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.modules.customers.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["customers"])

# Permiso oficial según matriz: clientes.gestionar (OWNER, SALES, TECHNICIAN, SW_DEV)
# El enunciado pide clientes.ver pero ese codename no existe en seeds; se usa gestionar.
ManageCustomers = Annotated[User, Depends(require_permission("clientes.gestionar"))]


@router.get("/customers/search", response_model=CustomerListResponse)
async def search_customers(
    db: DbSession,
    _: ManageCustomers,
    q: str = Query(..., min_length=1, description="Búsqueda rápida para POS"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> CustomerListResponse:
    """Búsqueda rápida de clientes para POS (por nombre, DNI, RUC, teléfono)."""
    items, total = await repository.list_customers(
        db, search=q, page=page, per_page=per_page
    )
    return CustomerListResponse(
        items=[CustomerResponse.from_model(c) for c in items], total=total
    )


@router.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    db: DbSession,
    _: ManageCustomers,
    search: str | None = Query(None, description="Filtro por nombre, DNI, RUC, teléfono"),
    q: str | None = Query(None, description="Alias de search para compatibilidad"),
    active: bool | None = Query(None),
    is_blocked: bool | None = Query(None),
    type: str | None = Query(None, description="PERSON | COMPANY"),  # noqa: A002
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> CustomerListResponse:
    term = search or q
    items, total = await repository.list_customers(
        db,
        search=term,
        active=active,
        is_blocked=is_blocked,
        type=type,
        page=page,
        per_page=per_page,
    )
    return CustomerListResponse(
        items=[CustomerResponse.from_model(c) for c in items], total=total
    )


@router.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer(
    body: CustomerCreate,
    db: DbSession,
    actor: ManageCustomers,
) -> CustomerResponse:
    customer = await service.create_customer(db, data=body, created_by=actor)
    return CustomerResponse.from_model(customer)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: DbSession,
    _: ManageCustomers,
) -> CustomerResponse:
    customer = await repository.get_by_id(db, customer_id)
    if customer is None:
        raise NotFoundError("Cliente no encontrado")
    return CustomerResponse.from_model(customer)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: uuid.UUID,
    body: CustomerUpdate,
    db: DbSession,
    actor: ManageCustomers,
) -> CustomerResponse:
    customer = await service.update_customer(
        db, customer_id=customer_id, data=body, updated_by=actor
    )
    return CustomerResponse.from_model(customer)

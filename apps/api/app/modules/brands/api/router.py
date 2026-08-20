"""Router de marcas."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.brands.application.schemas import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
)
from app.modules.brands.application.service import (
    create_brand,
    delete_brand,
    update_brand,
)
from app.modules.brands.domain.models import Brand
from app.modules.brands.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends

router = APIRouter(tags=["brands"])

ManageBrands = Annotated[User, Depends(require_permission("marcas.gestionar"))]


def _to_response(brand: Brand) -> BrandResponse:
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        logo_file_id=brand.logo_file_id,
        active=brand.active,
        created_at=brand.created_at,
    )


@router.get("/brands", response_model=list[BrandResponse])
async def list_brands(
    db: DbSession,
    include_inactive: bool = False,
) -> list[BrandResponse]:
    """Lista marcas (público; solo activas por defecto)."""
    brands = await repository.list_brands(
        db, active=None if include_inactive else True
    )
    return [_to_response(b) for b in brands]


@router.post("/brands", response_model=BrandResponse, status_code=201)
async def create_brand_endpoint(
    body: BrandCreate,
    db: DbSession,
    actor: ManageBrands,
) -> BrandResponse:
    """Crea una marca (solo OWNER)."""
    brand = await create_brand(db, data=body, created_by=actor)
    return _to_response(brand)


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand_endpoint(
    brand_id: uuid.UUID,
    body: BrandUpdate,
    db: DbSession,
    actor: ManageBrands,
) -> BrandResponse:
    """Actualiza una marca (solo OWNER)."""
    brand = await update_brand(db, brand_id=brand_id, data=body, updated_by=actor)
    return _to_response(brand)


@router.delete("/brands/{brand_id}", status_code=204)
async def delete_brand_endpoint(
    brand_id: uuid.UUID,
    db: DbSession,
    actor: ManageBrands,
) -> None:
    """Desactiva o elimina una marca (solo OWNER)."""
    await delete_brand(db, brand_id=brand_id, deleted_by=actor)

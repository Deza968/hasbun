"""Router de marcas (#F02-03). Público de lectura, OWNER para escritura."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.brands.application import service
from app.modules.brands.application.schemas import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
)
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["brands"])

ManageBrands = Annotated[User, Depends(require_permission("marcas.gestionar"))]


@router.get("/brands", response_model=list[BrandResponse])
async def list_brands(
    db: DbSession,
    include_inactive: bool = Query(False),
) -> list[BrandResponse]:
    """Lista marcas (público para tienda)."""
    brands = await service.list_brands(db, include_inactive=include_inactive)
    return [
        BrandResponse(
            id=b.id,
            name=b.name,
            slug=b.slug,
            logo_file_id=b.logo_file_id,
            active=b.active,
            created_at=b.created_at,
        )
        for b in brands
    ]


@router.post("/brands", response_model=BrandResponse, status_code=201)
async def create_brand(
    body: BrandCreate,
    db: DbSession,
    actor: ManageBrands,
) -> BrandResponse:
    brand = await service.create_brand(db, data=body, user=actor)
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        logo_file_id=brand.logo_file_id,
        active=brand.active,
        created_at=brand.created_at,
    )


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: uuid.UUID,
    body: BrandUpdate,
    db: DbSession,
    actor: ManageBrands,
) -> BrandResponse:
    brand = await service.update_brand(db, brand_id=brand_id, data=body, user=actor)
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        logo_file_id=brand.logo_file_id,
        active=brand.active,
        created_at=brand.created_at,
    )


@router.delete("/brands/{brand_id}", response_model=BrandResponse)
async def deactivate_brand(
    brand_id: uuid.UUID,
    db: DbSession,
    actor: ManageBrands,
) -> BrandResponse:
    brand = await service.deactivate_brand(db, brand_id=brand_id, user=actor)
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        slug=brand.slug,
        logo_file_id=brand.logo_file_id,
        active=brand.active,
        created_at=brand.created_at,
    )

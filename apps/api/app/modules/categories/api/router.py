"""Router de categorías (#F02-03). Público de lectura, OWNER para escritura."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.categories.application import service
from app.modules.categories.application.schemas import (
    CategoryCreate,
    CategoryNode,
    CategoryResponse,
    CategoryUpdate,
)
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends

router = APIRouter(tags=["categories"])

ManageCategories = Annotated[
    User, Depends(require_permission("categorias.gestionar"))
]


@router.get("/categories", response_model=list[CategoryNode])
async def list_categories_tree(db: DbSession) -> list[CategoryNode]:
    """Árbol jerárquico de categorías (público)."""
    categories = await service.list_categories(db)
    tree = service.build_tree(categories)
    return [CategoryNode(**node) for node in tree]


@router.get("/categories/flat", response_model=list[CategoryResponse])
async def list_categories_flat(db: DbSession) -> list[CategoryResponse]:
    """Lista plana (útil para selects)."""
    categories = await service.list_categories(db)
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            parent_id=c.parent_id,
            description=c.description,
            active=c.active,
            created_at=c.created_at,
        )
        for c in categories
    ]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    db: DbSession,
    actor: ManageCategories,
) -> CategoryResponse:
    category = await service.create_category(db, data=body, user=actor)
    return CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        active=category.active,
        created_at=category.created_at,
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    db: DbSession,
    actor: ManageCategories,
) -> CategoryResponse:
    category = await service.update_category(
        db, category_id=category_id, data=body, user=actor
    )
    return CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        active=category.active,
        created_at=category.created_at,
    )


@router.delete("/categories/{category_id}", response_model=CategoryResponse)
async def deactivate_category(
    category_id: uuid.UUID,
    db: DbSession,
    actor: ManageCategories,
) -> CategoryResponse:
    category = await service.deactivate_category(
        db, category_id=category_id, user=actor
    )
    return CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        active=category.active,
        created_at=category.created_at,
    )

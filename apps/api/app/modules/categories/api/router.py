"""Router de categorías."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.categories.application.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
)
from app.modules.categories.application.service import (
    build_tree,
    create_category,
    delete_category,
    update_category,
)
from app.modules.categories.domain.models import Category
from app.modules.categories.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends

router = APIRouter(tags=["categories"])

ManageCategories = Annotated[User, Depends(require_permission("categorias.gestionar"))]


def _to_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        description=category.description,
        active=category.active,
        created_at=category.created_at,
    )


def _to_tree(category: Category) -> CategoryTreeResponse:
    children = getattr(category, "_children", [])
    return CategoryTreeResponse(
        **_to_response(category).model_dump(),
        children=[_to_tree(child) for child in children],
    )


@router.get("/categories", response_model=list[CategoryTreeResponse])
async def list_categories(
    db: DbSession,
    include_inactive: bool = False,
) -> list[CategoryTreeResponse]:
    """Lista categorías como árbol jerárquico (público)."""
    categories = await repository.list_categories(
        db, active=None if include_inactive else True
    )
    return [_to_tree(c) for c in build_tree(categories)]


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category_endpoint(
    body: CategoryCreate,
    db: DbSession,
    actor: ManageCategories,
) -> CategoryResponse:
    """Crea una categoría (solo OWNER)."""
    category = await create_category(db, data=body, created_by=actor)
    return _to_response(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category_endpoint(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    db: DbSession,
    actor: ManageCategories,
) -> CategoryResponse:
    """Actualiza una categoría (solo OWNER)."""
    category = await update_category(
        db, category_id=category_id, data=body, updated_by=actor
    )
    return _to_response(category)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category_endpoint(
    category_id: uuid.UUID,
    db: DbSession,
    actor: ManageCategories,
) -> None:
    """Elimina una categoría; 409 si tiene productos activos (solo OWNER)."""
    await delete_category(db, category_id=category_id, deleted_by=actor)

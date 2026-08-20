"""Servicios de categorías."""

from __future__ import annotations

import uuid

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.utils import slugify
from app.modules.audit.application.service import log
from app.modules.categories.domain.models import Category
from app.modules.categories.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_category(
    db: AsyncSession, *, data, created_by: User
) -> Category:
    slug = slugify(data.name)
    if await repository.get_by_slug(db, slug):
        raise ConflictError(f"Ya existe una categoría con el nombre {data.name!r}")
    if data.parent_id is not None:
        parent = await repository.get_by_id(db, data.parent_id)
        if parent is None:
            raise NotFoundError("Categoría padre no encontrada")
    category = Category(
        name=data.name,
        slug=slug,
        parent_id=data.parent_id,
        description=data.description,
        active=True,
    )
    category = await repository.create(db, category)
    await log(
        action="CREATE_CATEGORY",
        module="products",
        user_id=created_by.id,
        entity_type="Category",
        entity_id=category.id,
        new_values={"name": category.name, "slug": category.slug},
    )
    return category


async def update_category(
    db: AsyncSession, *, category_id: uuid.UUID, data, updated_by: User
) -> Category:
    category = await repository.get_by_id(db, category_id)
    if category is None:
        raise NotFoundError("Categoría no encontrada")
    old = {"name": category.name, "active": category.active, "parent_id": category.parent_id}
    if data.name is not None:
        category.name = data.name
        category.slug = slugify(data.name)
    if data.parent_id is not None:
        if data.parent_id == category.id:
            raise BusinessRuleError("Una categoría no puede ser hija de sí misma")
        parent = await repository.get_by_id(db, data.parent_id)
        if parent is None:
            raise NotFoundError("Categoría padre no encontrada")
        category.parent_id = data.parent_id
    if data.description is not None:
        category.description = data.description
    if data.active is not None:
        category.active = data.active
    category = await repository.update(db, category)
    await log(
        action="UPDATE_CATEGORY",
        module="products",
        user_id=updated_by.id,
        entity_type="Category",
        entity_id=category.id,
        old_values=old,
        new_values={
            "name": category.name,
            "active": category.active,
            "parent_id": str(category.parent_id) if category.parent_id else None,
        },
    )
    return category


async def delete_category(
    db: AsyncSession, *, category_id: uuid.UUID, deleted_by: User
) -> None:
    """Elimina categoría; si tiene productos activos devuelve 409."""
    category = await repository.get_by_id(db, category_id)
    if category is None:
        raise NotFoundError("Categoría no encontrada")
    active_products = await repository.count_active_products(db, category_id)
    if active_products > 0:
        raise ConflictError(
            "No se puede eliminar una categoría con productos activos"
        )
    await db.delete(category)
    await db.commit()
    await log(
        action="DELETE_CATEGORY",
        module="products",
        user_id=deleted_by.id,
        entity_type="Category",
        entity_id=category_id,
    )


def build_tree(categories: list[Category]) -> list[Category]:
    """Arma el árbol jerárquico (categorías anidadas)."""
    nodes: dict[uuid.UUID, Category] = {c.id: c for c in categories}
    for category in categories:
        category._children = []
    roots: list[Category] = []
    for category in categories:
        if category.parent_id and category.parent_id in nodes:
            nodes[category.parent_id]._children.append(category)  # type: ignore[attr-defined]
        else:
            roots.append(category)
    return roots

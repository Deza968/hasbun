"""Servicio de categorías (#F02-03). Árbol jerárquico."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.audit.application.service import log
from app.modules.categories.domain.exceptions import (
    CategoryHasChildrenError,
    CategoryHasProductsError,
)
from app.modules.categories.domain.models import Category
from app.modules.users.domain.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SLUG_EXCLUDE = {"parent_id"}


def _slugify(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


async def _unique_slug(db: AsyncSession, name: str) -> str:
    base = _slugify(name) or "categoria"
    slug, counter = base, 1
    while True:
        exists = (
            await db.execute(select(Category).where(Category.slug == slug))
        ).scalars().first()
        if exists is None:
            return slug
        counter += 1
        slug = f"{base}-{counter}"


async def create_category(db: AsyncSession, *, data, user: User) -> Category:
    parent = None
    if data.parent_id:
        parent = await db.get(Category, data.parent_id)
        if parent is None:
            raise NotFoundError("Categoría padre no encontrada")
    category = Category(
        name=data.name,
        slug=await _unique_slug(db, data.name),
        parent_id=data.parent_id,
        description=data.description,
        active=True,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    await log(
        action="CREATE_CATEGORY",
        module="categories",
        user_id=user.id,
        entity_type="Category",
        entity_id=category.id,
        new_values={
            "name": category.name,
            "parent_id": str(category.parent_id) if category.parent_id else None,
        },
    )
    return category


async def list_categories(db: AsyncSession) -> list[Category]:
    return list(
        (await db.execute(select(Category).order_by(Category.name.asc()))).scalars().unique().all()
    )


def build_tree(categories: list[Category]) -> list[dict[str, object]]:
    """Convierte la lista plana en un árbol jerárquico (parent → children)."""
    by_id: dict[uuid.UUID, dict[str, object]] = {}
    for cat in categories:
        by_id[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "parent_id": cat.parent_id,
            "description": cat.description,
            "active": cat.active,
            "children": [],
        }
    roots: list[dict[str, object]] = []
    for cat in categories:
        node = by_id[cat.id]
        parent_node = by_id.get(cat.parent_id) if cat.parent_id else None
        if parent_node is None:
            roots.append(node)
        else:
            parent_node["children"].append(node)  # type: ignore[attr-defined]
    return roots


async def update_category(
    db: AsyncSession, *, category_id: uuid.UUID, data, user: User
) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Categoría no encontrada")
    if data.parent_id and data.parent_id == category_id:
        raise ConflictError("Una categoría no puede ser su propio padre")
    if data.parent_id:
        parent = await db.get(Category, data.parent_id)
        if parent is None:
            raise NotFoundError("Categoría padre no encontrada")
    old = {"name": category.name}
    if data.name is not None:
        category.name = data.name
        category.slug = await _unique_slug(db, data.name)
    if data.parent_id is not None:
        category.parent_id = data.parent_id
    if data.description is not None:
        category.description = data.description
    if data.active is not None:
        category.active = data.active
    await db.commit()
    await db.refresh(category)
    await log(
        action="UPDATE_CATEGORY",
        module="categories",
        user_id=user.id,
        entity_type="Category",
        entity_id=category.id,
        old_values=old,
        new_values={"name": category.name, "active": category.active},
    )
    return category


async def deactivate_category(
    db: AsyncSession, *, category_id: uuid.UUID, user: User
) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Categoría no encontrada")
    children = (
        await db.execute(select(Category).where(Category.parent_id == category_id))
    ).scalars().all()
    if children:
        raise CategoryHasChildrenError("La categoría tiene subcategorías")
    from app.modules.products.domain.models import Product

    products = (
        await db.execute(select(Product).where(Product.category_id == category_id))
    ).scalars().all()
    if products:
        raise CategoryHasProductsError("La categoría tiene productos activos")
    category.active = False
    await db.commit()
    await db.refresh(category)
    await log(
        action="DEACTIVATE_CATEGORY",
        module="categories",
        user_id=user.id,
        entity_type="Category",
        entity_id=category.id,
        new_values={"active": False},
    )
    return category

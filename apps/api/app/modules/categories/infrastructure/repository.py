"""Repository de categorías."""

from __future__ import annotations

import uuid

from app.modules.categories.domain.models import Category
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, category_id: uuid.UUID) -> Category | None:
    return await db.get(Category, category_id)


async def get_by_slug(db: AsyncSession, slug: str) -> Category | None:
    return (
        await db.execute(select(Category).where(Category.slug == slug))
    ).scalar_one_or_none()


async def list_categories(
    db: AsyncSession, *, active: bool | None = None
) -> list[Category]:
    query = select(Category)
    if active is not None:
        query = query.where(Category.active == active)
    return list((await db.execute(query.order_by(Category.name))).scalars().all())


async def count_products(db: AsyncSession, category_id: uuid.UUID) -> int:
    from app.modules.products.domain.models import Product

    return (
        await db.execute(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        )
    ).scalar_one()


async def count_active_products(db: AsyncSession, category_id: uuid.UUID) -> int:
    from app.modules.products.domain.models import Product

    return (
        await db.execute(
            select(func.count(Product.id)).where(
                Product.category_id == category_id, Product.active.is_(True)
            )
        )
    ).scalar_one()


async def create(db: AsyncSession, category: Category) -> Category:
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update(db: AsyncSession, category: Category) -> Category:
    await db.commit()
    await db.refresh(category)
    return category

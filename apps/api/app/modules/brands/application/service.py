"""Servicio de marcas (#F02-03)."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.audit.application.service import log
from app.modules.brands.domain.models import Brand
from app.modules.users.domain.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _slugify(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


async def _unique_brand_slug(db: AsyncSession, name: str) -> str:
    base = _slugify(name) or "marca"
    slug, counter = base, 1
    while True:
        exists = (
            await db.execute(select(Brand).where(Brand.slug == slug))
        ).scalars().first()
        if exists is None:
            return slug
        counter += 1
        slug = f"{base}-{counter}"


async def create_brand(db: AsyncSession, *, data, user: User) -> Brand:
    dup = (await db.execute(select(Brand).where(Brand.name == data.name))).scalars().first()
    if dup is not None:
        raise ConflictError("Ya existe una marca con ese nombre")
    brand = Brand(
        name=data.name,
        slug=await _unique_brand_slug(db, data.name),
        logo_file_id=data.logo_file_id,
        active=True,
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    await log(
        action="CREATE_BRAND",
        module="brands",
        user_id=user.id,
        entity_type="Brand",
        entity_id=brand.id,
        new_values={"name": brand.name},
    )
    return brand


async def list_brands(db: AsyncSession, *, include_inactive: bool = False) -> list[Brand]:
    query = select(Brand)
    if not include_inactive:
        query = query.where(Brand.active.is_(True))
    query = query.order_by(Brand.name.asc())
    return list((await db.execute(query)).scalars().all())


async def update_brand(db: AsyncSession, *, brand_id: uuid.UUID, data, user: User) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise NotFoundError("Marca no encontrada")
    old = {"name": brand.name}
    if data.name is not None:
        dup = (
            await db.execute(select(Brand).where(Brand.name == data.name, Brand.id != brand.id))
        ).scalars().first()
        if dup is not None:
            raise ConflictError("Ya existe una marca con ese nombre")
        brand.name = data.name
        brand.slug = await _unique_brand_slug(db, data.name)
    if data.logo_file_id is not None:
        brand.logo_file_id = data.logo_file_id
    if data.active is not None:
        brand.active = data.active
    await db.commit()
    await db.refresh(brand)
    await log(
        action="UPDATE_BRAND",
        module="brands",
        user_id=user.id,
        entity_type="Brand",
        entity_id=brand.id,
        old_values=old,
        new_values={"name": brand.name, "active": brand.active},
    )
    return brand


async def deactivate_brand(db: AsyncSession, *, brand_id: uuid.UUID, user: User) -> Brand:
    brand = await db.get(Brand, brand_id)
    if brand is None:
        raise NotFoundError("Marca no encontrada")
    from app.modules.products.domain.models import Product

    products = (
        await db.execute(select(Product).where(Product.brand_id == brand_id))
    ).scalars().all()
    if products:
        from app.modules.brands.domain.exceptions import BrandHasProductsError

        raise BrandHasProductsError("La marca tiene productos asociados")
    brand.active = False
    await db.commit()
    await db.refresh(brand)
    await log(
        action="DEACTIVATE_BRAND",
        module="brands",
        user_id=user.id,
        entity_type="Brand",
        entity_id=brand.id,
        new_values={"active": False},
    )
    return brand

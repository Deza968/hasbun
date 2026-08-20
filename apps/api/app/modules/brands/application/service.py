"""Servicios de marcas."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.utils import slugify
from app.modules.audit.application.service import log
from app.modules.brands.domain.models import Brand
from app.modules.brands.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_brand(db: AsyncSession, *, data, created_by: User) -> Brand:
    slug = slugify(data.name)
    if await repository.get_by_slug(db, slug):
        raise ConflictError(f"Ya existe una marca con el nombre {data.name!r}")
    brand = Brand(name=data.name, slug=slug, logo_file_id=data.logo_file_id, active=True)
    brand = await repository.create(db, brand)
    await log(
        action="CREATE_BRAND",
        module="products",
        user_id=created_by.id,
        entity_type="Brand",
        entity_id=brand.id,
        new_values={"name": brand.name, "slug": brand.slug},
    )
    return brand


async def update_brand(
    db: AsyncSession, *, brand_id: uuid.UUID, data, updated_by: User
) -> Brand:
    brand = await repository.get_by_id(db, brand_id)
    if brand is None:
        raise NotFoundError("Marca no encontrada")
    old = {"name": brand.name, "active": brand.active}
    if data.name is not None:
        brand.name = data.name
        brand.slug = slugify(data.name)
    if data.logo_file_id is not None:
        brand.logo_file_id = data.logo_file_id
    if data.active is not None:
        brand.active = data.active
    brand = await repository.update(db, brand)
    await log(
        action="UPDATE_BRAND",
        module="products",
        user_id=updated_by.id,
        entity_type="Brand",
        entity_id=brand.id,
        old_values=old,
        new_values={"name": brand.name, "active": brand.active},
    )
    return brand


async def delete_brand(
    db: AsyncSession, *, brand_id: uuid.UUID, deleted_by: User
) -> None:
    """Soft delete: desactiva la marca; si tiene productos, no se elimina."""
    brand = await repository.get_by_id(db, brand_id)
    if brand is None:
        raise NotFoundError("Marca no encontrada")
    products = await repository.count_products(db, brand_id)
    if products > 0:
        brand.active = False
        await repository.update(db, brand)
    else:
        await db.delete(brand)
        await db.commit()
    await log(
        action="DELETE_BRAND",
        module="products",
        user_id=deleted_by.id,
        entity_type="Brand",
        entity_id=brand_id,
        new_values={"active": False},
    )

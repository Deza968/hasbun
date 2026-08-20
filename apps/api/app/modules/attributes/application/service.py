"""Servicio de atributos dinámicos (#F02-04)."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.modules.attributes.domain.exceptions import DuplicateAttributeValueError
from app.modules.attributes.domain.models import Attribute, AttributeValue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_attributes(db: AsyncSession) -> list[Attribute]:
    return list(
        (await db.execute(select(Attribute).order_by(Attribute.name.asc()))).scalars().all()
    )


async def get_attribute(db: AsyncSession, attribute_id: uuid.UUID) -> Attribute | None:
    return await db.get(Attribute, attribute_id)


async def create_attribute(
    db: AsyncSession, *, name: str, data_type: str, unit: str | None = None
) -> Attribute:
    attr = Attribute(name=name, data_type=data_type, unit=unit)
    db.add(attr)
    await db.commit()
    await db.refresh(attr)
    return attr


async def list_attribute_values(
    db: AsyncSession, *, attribute_id: uuid.UUID
) -> list[AttributeValue]:
    attr = await db.get(Attribute, attribute_id)
    if attr is None:
        raise NotFoundError("Atributo no encontrado")
    return list(attr.values)


async def add_attribute_value(
    db: AsyncSession, *, attribute_id: uuid.UUID, value: str
) -> AttributeValue:
    attr = await db.get(Attribute, attribute_id)
    if attr is None:
        raise NotFoundError("Atributo no encontrado")
    existing = (
        await db.execute(
            select(AttributeValue).where(
                AttributeValue.attribute_id == attribute_id,
                AttributeValue.value == value,
            )
        )
    ).scalars().first()
    if existing is not None:
        raise DuplicateAttributeValueError("Ese valor ya existe para el atributo")
    av = AttributeValue(attribute_id=attribute_id, value=value)
    db.add(av)
    await db.commit()
    await db.refresh(av)
    return av

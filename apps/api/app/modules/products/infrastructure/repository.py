"""Repository del catálogo: atributos, productos, seriales y ofertas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.modules.products.domain.models import (
    Attribute,
    AttributeValue,
    Product,
    ProductOffer,
    SerializedUnit,
    SkuSequence,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# ---------- Atributos ----------

async def get_attribute_by_name(db: AsyncSession, name: str) -> Attribute | None:
    return (
        await db.execute(select(Attribute).where(Attribute.name == name))
    ).scalar_one_or_none()


async def list_attributes(db: AsyncSession) -> list[Attribute]:
    return list(
        (await db.execute(select(Attribute).order_by(Attribute.name))).scalars().all()
    )


async def get_attribute_by_id(
    db: AsyncSession, attribute_id: uuid.UUID
) -> Attribute | None:
    return await db.get(Attribute, attribute_id)


async def get_attribute_value(
    db: AsyncSession, attribute_id: uuid.UUID, value: str
) -> AttributeValue | None:
    return (
        await db.execute(
            select(AttributeValue).where(
                AttributeValue.attribute_id == attribute_id,
                AttributeValue.value == value,
            )
        )
    ).scalar_one_or_none()


async def create_attribute(db: AsyncSession, attribute: Attribute) -> Attribute:
    db.add(attribute)
    await db.commit()
    await db.refresh(attribute)
    return attribute


async def create_attribute_value(
    db: AsyncSession, attribute_value: AttributeValue
) -> AttributeValue:
    db.add(attribute_value)
    await db.commit()
    await db.refresh(attribute_value)
    return attribute_value


# ---------- SKU ----------

async def next_sku_value(db: AsyncSession, prefix: str) -> int:
    """Reserva el siguiente valor de secuencia con bloqueo de fila (FOR UPDATE)."""
    result = await db.execute(
        select(SkuSequence)
        .where(SkuSequence.prefix == prefix)
        .with_for_update()
    )
    sequence = result.scalar_one_or_none()
    if sequence is None:
        sequence = SkuSequence(prefix=prefix, last_value=0)
        db.add(sequence)
        await db.flush()
    sequence.last_value += 1
    await db.flush()
    return sequence.last_value


# ---------- Productos ----------

async def get_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    return await db.get(Product, product_id)


async def get_by_sku(db: AsyncSession, sku: str) -> Product | None:
    return (
        await db.execute(select(Product).where(Product.sku == sku))
    ).scalar_one_or_none()


async def get_by_slug(db: AsyncSession, slug: str) -> Product | None:
    return (
        await db.execute(select(Product).where(Product.slug == slug))
    ).scalar_one_or_none()


async def get_by_barcode(db: AsyncSession, barcode: str) -> Product | None:
    return (
        await db.execute(select(Product).where(Product.barcode == barcode))
    ).scalar_one_or_none()


async def list_products(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
    active: bool | None = None,
    published: bool | None = None,
    public: bool = False,
) -> tuple[list[Product], int]:
    """Lista productos con filtros y paginación."""
    query = select(Product)
    count_query = select(func.count(Product.id))

    def apply_filters(q):
        if category_id is not None:
            q = q.where(Product.category_id == category_id)
        if brand_id is not None:
            q = q.where(Product.brand_id == brand_id)
        if search:
            like = f"%{search.lower()}%"
            q = q.where(
                func.lower(Product.name).like(like)
                | func.lower(Product.sku).like(like)
                | func.lower(Product.barcode).like(like)
            )
        if public:
            q = q.where(Product.active.is_(True), Product.published.is_(True))
        elif active is not None:
            q = q.where(Product.active == active)
        if published is not None and not public:
            q = q.where(Product.published == published)
        return q

    query = apply_filters(query)
    count_query = apply_filters(count_query)

    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(
            query.order_by(Product.created_at.desc()).offset(offset).limit(limit)
        )
    ).scalars().all()
    return list(rows), total


async def count_sales_for_product(db: AsyncSession, product_id: uuid.UUID) -> int:
    """Cuenta ventas activas de un producto (tablas de ventas llegan en FASE 04)."""
    return 0


async def create(db: AsyncSession, product: Product) -> Product:
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update[T](db: AsyncSession, entity: T) -> T:
    await db.commit()
    await db.refresh(entity)
    return entity


# ---------- Seriales ----------

async def get_serial_by_number(db: AsyncSession, serial_number: str) -> SerializedUnit | None:
    return (
        await db.execute(
            select(SerializedUnit).where(SerializedUnit.serial_number == serial_number)
        )
    ).scalar_one_or_none()


async def list_serials(
    db: AsyncSession, *, product_id: uuid.UUID
) -> list[SerializedUnit]:
    return list(
        (
            await db.execute(
                select(SerializedUnit)
                .where(SerializedUnit.product_id == product_id)
                .order_by(SerializedUnit.created_at)
            )
        ).scalars().all()
    )


async def create_serial(db: AsyncSession, unit: SerializedUnit) -> SerializedUnit:
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


# ---------- Ofertas ----------

async def get_active_offer(
    db: AsyncSession, *, product_id: uuid.UUID, now: datetime
) -> ProductOffer | None:
    return (
        await db.execute(
            select(ProductOffer)
            .where(
                ProductOffer.product_id == product_id,
                ProductOffer.active.is_(True),
                ProductOffer.start_at <= now,
                ProductOffer.end_at >= now,
            )
            .order_by(ProductOffer.created_at.desc())
        )
    ).scalar_one_or_none()


async def list_offers(
    db: AsyncSession, *, product_id: uuid.UUID
) -> list[ProductOffer]:
    return list(
        (
            await db.execute(
                select(ProductOffer)
                .where(ProductOffer.product_id == product_id)
                .order_by(ProductOffer.created_at.desc())
            )
        ).scalars().all()
    )


async def get_offer_by_id(
    db: AsyncSession, offer_id: uuid.UUID
) -> ProductOffer | None:
    return await db.get(ProductOffer, offer_id)


async def create_offer(db: AsyncSession, offer: ProductOffer) -> ProductOffer:
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


async def deactivate_offer(
    db: AsyncSession, offer: ProductOffer
) -> ProductOffer:
    offer.active = False
    await db.commit()
    await db.refresh(offer)
    return offer

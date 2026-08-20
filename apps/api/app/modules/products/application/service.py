"""Servicio de catálogo: productos, seriales, ofertas (FASE 02)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.attributes.domain.models import (
    Attribute,
    AttributeValue,
    ProductAttributeValue,
)
from app.modules.audit.application.service import log
from app.modules.brands.domain.models import Brand
from app.modules.categories.domain.models import Category
from app.modules.exchange_rates.application.service import get_current_rate
from app.modules.products.domain.exceptions import (
    DuplicateSerialNumberError,
    InvalidPriceRuleError,
    ProductHasActiveReferencesError,
)
from app.modules.products.domain.models import (
    Product,
    ProductImage,
    ProductOffer,
    SerializedUnit,
)
from app.modules.products.infrastructure import repository
from app.modules.products.infrastructure.sku import generate_sku, prefix_for_category
from app.modules.users.domain.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

VALID_PRICE_RULES = {"FIXED_PEN", "FIXED_USD", "USD_CONVERTED", "COST_USD_MARGIN", "MANUAL"}

SERIAL_STATUSES = {
    "AVAILABLE",
    "RESERVED",
    "PARTIALLY_PAID",
    "DELIVERED_ON_CREDIT",
    "SOLD",
    "IN_REPAIR",
    "RETURNED",
    "DAMAGED",
}


def _slugify(value: str) -> str:
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:100] or "producto"


async def _unique_slug(db: AsyncSession, name: str, exclude_id: uuid.UUID | None = None) -> str:
    base = _slugify(name)
    slug = base
    counter = 1
    while True:
        existing = await repository.get_by_slug(db, slug)
        if existing is None or (exclude_id and existing.id == exclude_id):
            return slug
        counter += 1
        slug = f"{base}-{counter}"


async def create_product(
    db: AsyncSession, *, data, created_by: User, prefix: str | None = None
) -> Product:
    """Crea producto con SKU automático (#F02-09)."""
    if data.price_rule not in VALID_PRICE_RULES:
        raise InvalidPriceRuleError(f"Regla de precio inválida: {data.price_rule}")

    category = None
    if data.category_id:
        category = await db.get(Category, data.category_id)
        if category is None:
            raise NotFoundError("Categoría no encontrada")

    brand = None
    if data.brand_id:
        brand = await db.get(Brand, data.brand_id)
        if brand is None:
            raise NotFoundError("Marca no encontrada")

    resolved_prefix = prefix or prefix_for_category(category.slug if category else None)
    sku = await generate_sku(db, resolved_prefix)
    slug = await _unique_slug(db, data.name)

    product = Product(
        sku=sku,
        barcode=data.barcode,
        name=data.name,
        slug=slug,
        description=data.description,
        short_description=data.short_description,
        brand_id=data.brand_id,
        category_id=data.category_id,
        cost_price=data.cost_price,
        sale_price=data.sale_price,
        currency=data.currency,
        price_rule=data.price_rule,
        active=True,
        published=data.published or False,
        stock_minimum=data.stock_minimum,
        is_serialized=data.is_serialized,
        weight_kg=data.weight_kg,
        notes=data.notes,
    )

    db.add(product)
    await db.flush()

    if data.attribute_links:
        await _assign_attributes(db, product, data.attribute_links)

    if data.serials:
        if not product.is_serialized:
            raise ValidationError(
                "El producto no está marcado como serializado y no acepta seriales"
            )
        for serial in data.serials:
            await _register_serial(db, product, serial, created_by)

    await db.commit()
    await db.refresh(product)

    await log(
        action="CREATE_PRODUCT",
        module="products",
        user_id=created_by.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={"sku": product.sku, "name": product.name, "price": str(product.sale_price)},
    )
    return product


async def _assign_attributes(
    db: AsyncSession, product: Product, pairs: list[dict[str, Any]]
) -> None:
    """Crea/vincula valores de atributos dinámicos al producto (#F02-04)."""
    for pair in pairs:
        attr_name = (pair.get("attribute") or "").strip()
        value_text = (pair.get("value") or "").strip()
        if not attr_name or not value_text:
            raise ValidationError("Atributos inválidos: falta attribute o value")

        attribute = (
            await db.execute(select(Attribute).where(Attribute.name == attr_name))
        ).scalars().first()
        if attribute is None:
            attribute = Attribute(
                name=attr_name,
                data_type=pair.get("data_type", "text"),
                unit=pair.get("unit"),
            )
            db.add(attribute)
            await db.flush()

        av = (
            await db.execute(
                select(AttributeValue).where(
                    AttributeValue.attribute_id == attribute.id,
                    AttributeValue.value == value_text,
                )
            )
        ).scalars().first()
        if av is None:
            av = AttributeValue(attribute_id=attribute.id, value=value_text)
            db.add(av)
            await db.flush()

        link = (
            await db.execute(
                select(ProductAttributeValue).where(
                    ProductAttributeValue.product_id == product.id,
                    ProductAttributeValue.attribute_value_id == av.id,
                )
            )
        ).scalars().first()
        if link is None:
            db.add(ProductAttributeValue(product_id=product.id, attribute_value_id=av.id))
            await db.flush()


async def update_product(
    db: AsyncSession, *, product_id: uuid.UUID, data, updated_by: User
) -> Product:
    """Actualiza producto; audita cambios de costo/precio (#F02-09)."""
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")

    old_values: dict[str, str | None] = {}
    new_values: dict[str, str | None] = {}
    for field in ("cost_price", "sale_price"):
        current = getattr(product, field)
        incoming = getattr(data, field, None)
        if incoming is not None and current != incoming:
            old_values[field] = str(current)
            new_values[field] = str(incoming)

    changed_sensitive = bool(new_values)

    for field, value in data.model_dump(exclude_unset=True).items():
        if field in {"cost_price", "sale_price"}:
            if value is not None:
                setattr(product, field, value)
        else:
            setattr(product, field, value)

    if getattr(data, "name", None) and data.name != product.name:
        product.slug = await _unique_slug(db, data.name, exclude_id=product.id)

    if changed_sensitive:
        await log(
            action="UPDATE_PRODUCT_PRICE",
            module="products",
            user_id=updated_by.id,
            entity_type="Product",
            entity_id=product.id,
            old_values=old_values,
            new_values=new_values,
        )

    await db.commit()
    await db.refresh(product)
    await log(
        action="UPDATE_PRODUCT",
        module="products",
        user_id=updated_by.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={"name": product.name, "sku": product.sku},
    )
    return product


async def assign_attributes(
    db: AsyncSession, *, product_id: uuid.UUID, pairs: list[dict[str, Any]], updated_by: User
) -> Product:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    await _assign_attributes(db, product, pairs)
    await db.commit()
    await db.refresh(product)
    await log(
        action="ASSIGN_PRODUCT_ATTRIBUTES",
        module="products",
        user_id=updated_by.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={"attributes": pairs},
    )
    return product


async def deactivate_product(
    db: AsyncSession, *, product_id: uuid.UUID, deactivated_by: User
) -> Product:
    """Desactiva producto (soft delete). No elimina físicamente (#F02-09)."""
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    if await _has_active_references(db, product_id):
        raise ProductHasActiveReferencesError(
            "El producto tiene ventas, movimientos o reparaciones activas"
        )
    product.active = False
    await db.commit()
    await db.refresh(product)
    await log(
        action="DEACTIVATE_PRODUCT",
        module="products",
        user_id=deactivated_by.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={"active": False},
    )
    return product


async def _has_active_references(db: AsyncSession, product_id: uuid.UUID) -> bool:
    """Verificación simple: ventas/movimientos se integran en FASE 03/04."""
    # TODO(FASE 03/04): consultar sales, inventory_movements, repair_part_usages.
    return False


async def publish_product(
    db: AsyncSession, *, product_id: uuid.UUID, published: bool, user: User
) -> Product:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    product.published = published
    await db.commit()
    await db.refresh(product)
    await log(
        action="PUBLISH_PRODUCT" if published else "UNPUBLISH_PRODUCT",
        module="products",
        user_id=user.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={"published": published},
    )
    return product


async def get_current_price(
    db: AsyncSession, product: Product, now: datetime | None = None
) -> dict[str, object]:
    """Precio vigente considerando ofertas activas y tipo de cambio (#F02-08)."""
    now = now or datetime.now(UTC)
    active_offer: ProductOffer | None = None
    for offer in product.offers:
        if (
            offer.active
            and offer.start_at <= now
            and offer.end_at >= now
        ):
            active_offer = offer
            break

    price = product.sale_price
    currency = product.currency
    source = "sale_price"

    if active_offer is not None:
        price = active_offer.offer_price
        source = "offer"

    if product.price_rule == "USD_CONVERTED" or currency == "USD":
        rate = await get_current_rate(db, from_currency="USD", to_currency="PEN")
        price = (price * rate.rate).quantize(Decimal("0.01"))
        currency = "PEN"

    return {"price": price, "currency": currency, "source": source}


async def _register_serial(
    db: AsyncSession, product: Product, data, actor: User
) -> SerializedUnit:
    duplicate = (
        await db.execute(
            select(SerializedUnit).where(
                SerializedUnit.serial_number == data.serial_number
            )
        )
    ).scalars().first()
    if duplicate is not None:
        raise DuplicateSerialNumberError("Ese número de serie ya está registrado")
    if data.imei:
        dup_imei = (
            await db.execute(select(SerializedUnit).where(SerializedUnit.imei == data.imei))
        ).scalars().first()
        if dup_imei is not None:
            raise DuplicateSerialNumberError("Ese IMEI ya está registrado")

    unit = SerializedUnit(
        product_id=product.id,
        serial_number=data.serial_number,
        imei=data.imei,
        imei2=data.imei2,
        mac_address=data.mac_address,
        status=data.status or "AVAILABLE",
        notes=data.notes,
    )
    db.add(unit)
    await db.flush()
    return unit


async def register_serial(
    db: AsyncSession, *, product_id: uuid.UUID, data, user: User
) -> SerializedUnit:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    if not product.is_serialized:
        raise ValidationError("El producto no es serializado")
    if data.status not in SERIAL_STATUSES:
        raise ValidationError(f"Estado inválido: {data.status}")
    unit = await _register_serial(db, product, data, user)
    await db.commit()
    await db.refresh(unit)
    await log(
        action="REGISTER_SERIAL",
        module="products",
        user_id=user.id,
        entity_type="SerializedUnit",
        entity_id=unit.id,
        new_values={"serial": unit.serial_number, "status": unit.status},
    )
    return unit


async def update_serial_status(
    db: AsyncSession, *, serial_id: uuid.UUID, status: str, user: User
) -> SerializedUnit:
    unit = await db.get(SerializedUnit, serial_id)
    if unit is None:
        raise NotFoundError("Serie no encontrada")
    if status not in SERIAL_STATUSES:
        raise ValidationError(f"Estado inválido: {status}")
    old = unit.status
    new = status
    unit.status = new
    await db.commit()
    await db.refresh(unit)
    await log(
        action="UPDATE_SERIAL_STATUS",
        module="products",
        user_id=user.id,
        entity_type="SerializedUnit",
        entity_id=unit.id,
        old_values={"status": old},
        new_values={"status": new},
    )
    return unit


async def create_offer(
    db: AsyncSession, *, product_id: uuid.UUID, data, user: User
) -> ProductOffer:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    if data.offer_price >= data.normal_price:
        raise ValidationError("offer_price debe ser menor a normal_price")
    if data.end_at <= data.start_at:
        raise ValidationError("end_at debe ser posterior a start_at")
    offer = ProductOffer(
        product_id=product.id,
        normal_price=data.normal_price,
        offer_price=data.offer_price,
        start_at=data.start_at,
        end_at=data.end_at,
        active=True,
        created_by=user.id,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    await log(
        action="CREATE_OFFER",
        module="products",
        user_id=user.id,
        entity_type="ProductOffer",
        entity_id=offer.id,
        new_values={
            "normal_price": str(offer.normal_price),
            "offer_price": str(offer.offer_price),
            "start_at": offer.start_at.isoformat(),
            "end_at": offer.end_at.isoformat(),
        },
    )
    return offer


async def deactivate_offer(
    db: AsyncSession, *, offer_id: uuid.UUID, user: User
) -> ProductOffer:
    offer = await db.get(ProductOffer, offer_id)
    if offer is None:
        raise NotFoundError("Oferta no encontrada")
    offer.active = False
    await db.commit()
    await db.refresh(offer)
    await log(
        action="DEACTIVATE_OFFER",
        module="products",
        user_id=user.id,
        entity_type="ProductOffer",
        entity_id=offer.id,
        new_values={"active": False},
    )
    return offer


async def add_product_image(
    db: AsyncSession, *, product_id: uuid.UUID, file_id: uuid.UUID, user: User
) -> ProductImage:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")

    count = (
        await db.execute(
            select(ProductImage).where(ProductImage.product_id == product_id)
        )
    ).scalars().all()
    is_primary = len(count) == 0
    image = ProductImage(
        product_id=product_id,
        file_id=file_id,
        display_order=len(count),
        is_primary=is_primary,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    await log(
        action="ADD_PRODUCT_IMAGE",
        module="products",
        user_id=user.id,
        entity_type="ProductImage",
        entity_id=image.id,
        new_values={"product_id": str(product_id), "file_id": str(file_id)},
    )
    return image


async def list_product_images(
    db: AsyncSession, *, product_id: uuid.UUID
) -> list[ProductImage]:
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
        .order_by(ProductImage.display_order.asc())
    )
    return list(result.scalars().all())


async def mark_image_primary(
    db: AsyncSession, *, image_id: uuid.UUID, user: User
) -> ProductImage:
    image = await db.get(ProductImage, image_id)
    if image is None:
        raise NotFoundError("Imagen no encontrada")
    images = await list_product_images(db, product_id=image.product_id)
    for img in images:
        img.is_primary = img.id == image.id
    await db.commit()
    await log(
        action="SET_PRIMARY_IMAGE",
        module="products",
        user_id=user.id,
        entity_type="ProductImage",
        entity_id=image.id,
        new_values={"is_primary": True},
    )
    return image


async def remove_product_image(
    db: AsyncSession, *, image_id: uuid.UUID, user: User
) -> None:
    image = await db.get(ProductImage, image_id)
    if image is None:
        raise NotFoundError("Imagen no encontrada")
    await db.delete(image)
    await db.commit()
    await log(
        action="REMOVE_PRODUCT_IMAGE",
        module="products",
        user_id=user.id,
        entity_type="ProductImage",
        entity_id=image_id,
        old_values={"file_id": str(image.file_id)},
    )

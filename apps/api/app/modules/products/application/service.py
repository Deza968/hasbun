"""Servicios del catálogo de productos."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from app.core.utils import slugify
from app.modules.audit.application.service import log
from app.modules.categories.infrastructure import repository as categories_repo
from app.modules.products.domain.models import (
    Attribute,
    AttributeValue,
    Product,
    ProductImage,
    ProductOffer,
    SerializedUnit,
    SerialUnitStatus,
)
from app.modules.products.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession

# Prefijos de SKU por categoría (configurable). Orden de coincidencia por slug.
SKU_PREFIX_RULES: list[tuple[list[str], str]] = [
    (["laptop", "computadora", "computo", "pc"], "LAP"),
    (["impresora", "impresion"], "IMP"),
    (["camara", "camera"], "CAM"),
    (["accesorio"], "ACC"),
    (["electrodomestic", "televisor", "tv", "refrigeradora"], "ELE"),
    (["servicio"], "SRV"),
    (["sublimaci"], "SBL"),
    (["monitor"], "MON"),
    (["celular", "telefono", "smartphone"], "CEL"),
    (["tablet"], "TAB"),
    (["red", "router", "modem", "wifi"], "RED"),
    (["almacenamiento", "disco"], "ALM"),
]


def get_sku_prefix(category_name: str | None) -> str:
    """Determina el prefijo del SKU según la categoría del producto."""
    if category_name:
        name_lower = category_name.lower()
        for keywords, prefix in SKU_PREFIX_RULES:
            if any(keyword in name_lower for keyword in keywords):
                return prefix
    return "PRO"


async def generate_sku(db: AsyncSession, prefix: str) -> str:
    """Genera un SKU único de forma transaccional (FOR UPDATE)."""
    value = await repository.next_sku_value(db, prefix)
    return f"{prefix}-{value:05d}"


async def create_product(db: AsyncSession, *, data, created_by: User) -> Product:
    category_name = (
        await _category_name(db, data.category_id) if data.category_id else None
    )
    prefix = get_sku_prefix(category_name)
    sku = await generate_sku(db, prefix)
    slug = slugify(data.name)
    existing = await repository.get_by_slug(db, slug)
    if existing is not None:
        slug = f"{slug}-{sku.lower()}"

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
        published=False,
        stock_minimum=data.stock_minimum,
        is_serialized=data.is_serialized,
        weight_kg=data.weight_kg,
        notes=data.notes,
    )
    product = await repository.create(db, product)

    if data.attributes:
        await _attach_attributes(db, product, data.attributes)

    await log(
        action="CREATE_PRODUCT",
        module="products",
        user_id=created_by.id,
        entity_type="Product",
        entity_id=product.id,
        new_values={
            "sku": product.sku,
            "name": product.name,
            "cost_price": str(product.cost_price),
            "sale_price": str(product.sale_price),
        },
    )
    return product


async def _category_name(db: AsyncSession, category_id: uuid.UUID) -> str | None:
    category = await categories_repo.get_by_id(db, category_id)
    return category.name if category else None


async def update_product(
    db: AsyncSession, *, product_id: uuid.UUID, data, updated_by: User
) -> Product:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")

    old = {
        "cost_price": str(product.cost_price),
        "sale_price": str(product.sale_price),
        "name": product.name,
        "active": product.active,
    }
    if data.name is not None:
        product.name = data.name
        product.slug = slugify(data.name)
    if data.barcode is not None:
        product.barcode = data.barcode
    if data.description is not None:
        product.description = data.description
    if data.short_description is not None:
        product.short_description = data.short_description
    if data.brand_id is not None:
        product.brand_id = data.brand_id
    if data.category_id is not None:
        product.category_id = data.category_id
    if data.cost_price is not None:
        product.cost_price = data.cost_price
    if data.sale_price is not None:
        product.sale_price = data.sale_price
    if data.currency is not None:
        product.currency = data.currency
    if data.price_rule is not None:
        product.price_rule = data.price_rule
    if data.stock_minimum is not None:
        product.stock_minimum = data.stock_minimum
    if data.is_serialized is not None:
        product.is_serialized = data.is_serialized
    if data.weight_kg is not None:
        product.weight_kg = data.weight_kg
    if data.notes is not None:
        product.notes = data.notes
    if data.active is not None:
        product.active = data.active

    product = await repository.update(db, product)
    price_changed = (
        str(old["cost_price"]) != str(product.cost_price)
        or str(old["sale_price"]) != str(product.sale_price)
    )
    await log(
        action="UPDATE_PRODUCT",
        module="products",
        user_id=updated_by.id,
        entity_type="Product",
        entity_id=product.id,
        old_values=old,
        new_values={
            "cost_price": str(product.cost_price),
            "sale_price": str(product.sale_price),
            "name": product.name,
            "active": product.active,
        },
    )
    if price_changed:
        await log(
            action="PRODUCT_PRICE_CHANGED",
            module="products",
            user_id=updated_by.id,
            entity_type="Product",
            entity_id=product.id,
            old_values={"cost_price": old["cost_price"], "sale_price": old["sale_price"]},
            new_values={
                "cost_price": str(product.cost_price),
                "sale_price": str(product.sale_price),
            },
        )
    return product


async def deactivate_product(
    db: AsyncSession, *, product_id: uuid.UUID, deactivated_by: User
) -> None:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    if await repository.count_sales_for_product(db, product_id) > 0:
        raise ConflictError("No se puede desactivar un producto con ventas activas")
    product.active = False
    product.published = False
    await repository.update(db, product)
    await log(
        action="DEACTIVATE_PRODUCT",
        module="products",
        user_id=deactivated_by.id,
        entity_type="Product",
        entity_id=product_id,
    )


async def set_published(
    db: AsyncSession, *, product_id: uuid.UUID, published: bool, actor: User
) -> Product:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    product.published = published
    product = await repository.update(db, product)
    await log(
        action="PUBLISH_PRODUCT" if published else "UNPUBLISH_PRODUCT",
        module="products",
        user_id=actor.id,
        entity_type="Product",
        entity_id=product_id,
    )
    return product


async def get_current_price(
    db: AsyncSession, product: Product, *, now: datetime | None = None
) -> tuple[ProductOffer | None, Decimal]:
    """Retorna (oferta activa, precio vigente). Oferta > sale_price."""
    now = now or datetime.now(UTC)
    offer = await repository.get_active_offer(db, product_id=product.id, now=now)
    if offer is not None:
        return offer, offer.offer_price
    return None, product.sale_price


# ---------- Atributos ----------

async def _attach_attributes(db: AsyncSession, product: Product, attributes) -> None:
    for item in attributes:
        attribute_value = await repository.get_attribute_value(
            db, item.attribute_id, item.value
        )
        if attribute_value is None:
            attribute_value = AttributeValue(
                attribute_id=item.attribute_id, value=item.value
            )
            attribute_value = await repository.create_attribute_value(db, attribute_value)
        if attribute_value not in product.attribute_values:
            product.attribute_values.append(attribute_value)
    await repository.update(db, product)


async def set_product_attributes(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    attributes,
    updated_by: User,
) -> Product:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    product.attribute_values = []
    await db.flush()
    await _attach_attributes(db, product, attributes)
    await log(
        action="UPDATE_PRODUCT_ATTRIBUTES",
        module="products",
        user_id=updated_by.id,
        entity_type="Product",
        entity_id=product_id,
        new_values={
            "attributes": [f"{a.attribute_id}:{a.value}" for a in attributes]
        },
    )
    return product


async def create_attribute(
    db: AsyncSession, *, data, created_by: User
) -> Attribute:
    attribute = await repository.get_attribute_by_name(db, data.name)
    if attribute is not None:
        raise ConflictError(f"Ya existe el atributo {data.name!r}")
    attribute = Attribute(
        name=data.name, data_type=data.data_type, unit=data.unit
    )
    attribute = await repository.create_attribute(db, attribute)
    await log(
        action="CREATE_ATTRIBUTE",
        module="products",
        user_id=created_by.id,
        entity_type="Attribute",
        entity_id=attribute.id,
        new_values={"name": attribute.name, "data_type": attribute.data_type.value},
    )
    return attribute


async def add_attribute_value(
    db: AsyncSession, *, attribute_id: uuid.UUID, value: str, created_by: User
) -> AttributeValue:
    attribute = await repository.get_attribute_by_id(db, attribute_id)
    if attribute is None:
        raise NotFoundError("Atributo no encontrado")
    if await repository.get_attribute_value(db, attribute_id, value):
        raise ConflictError(f"El valor {value!r} ya existe para este atributo")
    attribute_value = AttributeValue(attribute_id=attribute_id, value=value)
    attribute_value = await repository.create_attribute_value(db, attribute_value)
    await log(
        action="CREATE_ATTRIBUTE_VALUE",
        module="products",
        user_id=created_by.id,
        entity_type="AttributeValue",
        entity_id=attribute_value.id,
        new_values={"attribute_id": str(attribute_id), "value": value},
    )
    return attribute_value


# ---------- Seriales ----------

async def register_serial(
    db: AsyncSession, *, product_id: uuid.UUID, data, created_by: User
) -> SerializedUnit:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    if not product.is_serialized:
        raise BusinessRuleError("El producto no está marcado como serializado")
    if await repository.get_serial_by_number(db, data.serial_number):
        raise ConflictError("Ya existe una unidad con ese número de serial")
    unit = SerializedUnit(
        product_id=product_id,
        serial_number=data.serial_number,
        imei=data.imei,
        imei2=data.imei2,
        mac_address=data.mac_address,
        status=SerialUnitStatus.AVAILABLE,
        notes=data.notes,
    )
    unit = await repository.create_serial(db, unit)
    await log(
        action="REGISTER_SERIAL",
        module="products",
        user_id=created_by.id,
        entity_type="SerializedUnit",
        entity_id=unit.id,
        new_values={"serial_number": unit.serial_number, "product_id": str(product_id)},
    )
    return unit


async def update_serial_status(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    serial_id: uuid.UUID,
    status: SerialUnitStatus,
    notes: str | None,
    updated_by: User,
) -> SerializedUnit:
    serials = await repository.list_serials(db, product_id=product_id)
    unit = next((s for s in serials if s.id == serial_id), None)
    if unit is None:
        raise NotFoundError("Serial no encontrado")
    old_status = unit.status
    unit.status = status
    if notes is not None:
        unit.notes = notes
    await repository.update(db, unit)
    await log(
        action="UPDATE_SERIAL_STATUS",
        module="products",
        user_id=updated_by.id,
        entity_type="SerializedUnit",
        entity_id=unit.id,
        old_values={"status": old_status.value},
        new_values={"status": status.value},
    )
    return unit


# ---------- Ofertas ----------

async def create_offer(
    db: AsyncSession, *, product_id: uuid.UUID, data, created_by: User
) -> ProductOffer:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    offer = ProductOffer(
        product_id=product_id,
        normal_price=data.normal_price,
        offer_price=data.offer_price,
        start_at=data.start_at,
        end_at=data.end_at,
        active=True,
        created_by=created_by.id,
    )
    offer = await repository.create_offer(db, offer)
    await log(
        action="CREATE_OFFER",
        module="products",
        user_id=created_by.id,
        entity_type="ProductOffer",
        entity_id=offer.id,
        new_values={
            "product_id": str(product_id),
            "normal_price": str(offer.normal_price),
            "offer_price": str(offer.offer_price),
        },
    )
    return offer


async def deactivate_offer(
    db: AsyncSession, *, product_id: uuid.UUID, offer_id: uuid.UUID, actor: User
) -> None:
    offer = await repository.get_offer_by_id(db, offer_id)
    if offer is None or offer.product_id != product_id:
        raise NotFoundError("Oferta no encontrada")
    await repository.deactivate_offer(db, offer)
    await log(
        action="DEACTIVATE_OFFER",
        module="products",
        user_id=actor.id,
        entity_type="ProductOffer",
        entity_id=offer_id,
    )


# ---------- Imágenes ----------

async def add_product_image(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    data: bytes,
    filename: str,
    mime_type: str | None,
    actor: User,
) -> ProductImage:
    """Sube una imagen y la asocia al producto."""
    from app.modules.files.application.service import upload_file

    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")

    file_obj = await upload_file(
        db, filename=filename, data=data, mime_type=mime_type, uploaded_by=actor
    )
    display_order = max((img.display_order for img in product.images), default=-1) + 1
    image = ProductImage(
        product_id=product_id,
        file_id=file_obj.id,
        display_order=display_order,
        is_primary=not product.images,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    await log(
        action="ADD_PRODUCT_IMAGE",
        module="products",
        user_id=actor.id,
        entity_type="ProductImage",
        entity_id=image.id,
        new_values={"product_id": str(product_id), "file_id": str(file_obj.id)},
    )
    return image


async def set_primary_image(
    db: AsyncSession, *, product_id: uuid.UUID, image_id: uuid.UUID, actor: User
) -> None:
    from sqlalchemy import update as sql_update

    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    image = next((img for img in product.images if img.id == image_id), None)
    if image is None:
        raise NotFoundError("Imagen no encontrada")
    await db.execute(
        sql_update(ProductImage)
        .where(ProductImage.product_id == product_id)
        .values(is_primary=False)
    )
    image.is_primary = True
    await db.commit()
    await log(
        action="SET_PRIMARY_IMAGE",
        module="products",
        user_id=actor.id,
        entity_type="ProductImage",
        entity_id=image_id,
        new_values={"product_id": str(product_id)},
    )


async def remove_product_image(
    db: AsyncSession, *, product_id: uuid.UUID, image_id: uuid.UUID, actor: User
) -> None:
    from app.modules.files.application.service import delete_file
    from sqlalchemy import delete as sql_delete

    product = await repository.get_by_id(db, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    image = next((img for img in product.images if img.id == image_id), None)
    if image is None:
        raise NotFoundError("Imagen no encontrada")
    was_primary = image.is_primary
    await db.execute(sql_delete(ProductImage).where(ProductImage.id == image_id))
    await db.commit()
    await delete_file(db, file_id=image.file_id, deleted_by=actor)
    if was_primary:
        remaining = await repository.get_by_id(db, product_id)
        if remaining and remaining.images:
            remaining.images[0].is_primary = True
            await db.commit()
    await log(
        action="REMOVE_PRODUCT_IMAGE",
        module="products",
        user_id=actor.id,
        entity_type="ProductImage",
        entity_id=image_id,
        new_values={"product_id": str(product_id)},
    )

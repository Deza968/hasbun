"""Seed del catálogo de FASE 02: tipo de cambio, marcas, categorías, atributos y productos."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import slugify
from app.modules.brands.domain.models import Brand
from app.modules.categories.domain.models import Category
from app.modules.exchange_rates.domain.models import ExchangeRate
from app.modules.products.application.schemas import ProductAttributeInput, ProductCreate
from app.modules.products.application.service import (
    add_attribute_value,
    create_attribute,
    create_product,
)
from app.modules.products.domain.models import Attribute, AttributeDataType, PriceRule
from app.modules.users.domain.models import User

BRANDS = [
    "HP",
    "Lenovo",
    "Dell",
    "ASUS",
    "Apple",
    "Samsung",
    "Canon",
    "Epson",
    "Brother",
    "TP-Link",
    "Kingston",
    "Xiaomi",
    "LG",
    "Sony",
    "Logitech",
]

# (nombre, slug de categoría padre)
CATEGORIES: list[tuple[str, str | None]] = [
    ("Laptops y Computadoras", None),
    ("Laptops", "Laptops y Computadoras"),
    ("Desktops", "Laptops y Computadoras"),
    ("Impresoras", None),
    ("Cámaras y Seguridad", None),
    ("Cámaras", "Cámaras y Seguridad"),
    ("Cámaras de Seguridad", "Cámaras y Seguridad"),
    ("Accesorios", None),
    ("Teclados", "Accesorios"),
    ("Mouses", "Accesorios"),
    ("Audífonos", "Accesorios"),
    ("Cables", "Accesorios"),
    ("Electrodomésticos", None),
    ("Televisores", "Electrodomésticos"),
    ("Refrigeradoras", "Electrodomésticos"),
    ("Servicios", None),
    ("Servicios de Instalación", "Servicios"),
    ("Servicios de Reparación", "Servicios"),
    ("Sublimación", None),
    ("Papel de Sublimación", "Sublimación"),
    ("Tazas de Sublimación", "Sublimación"),
    ("Monitores", None),
    ("Celulares y Tablets", None),
    ("Celulares", "Celulares y Tablets"),
    ("Tablets", "Celulares y Tablets"),
    ("Redes y Comunicaciones", None),
    ("Routers", "Redes y Comunicaciones"),
    ("Módems", "Redes y Comunicaciones"),
    ("Switches", "Redes y Comunicaciones"),
    ("Almacenamiento", None),
    ("Discos SSD", "Almacenamiento"),
    ("Discos HDD Externos", "Almacenamiento"),
]

ATTRIBUTES: dict[str, tuple[AttributeDataType, list[str]]] = {
    "Color": (AttributeDataType.list_, ["Negro", "Blanco", "Plateado", "Azul", "Rojo"]),
    "Capacidad": (AttributeDataType.list_, ["128GB", "256GB", "512GB", "1TB", "2TB"]),
    "Garantía": (AttributeDataType.list_, ["6 meses", "1 año", "2 años"]),
}

PRODUCTS: list[dict] = [
    {
        "name": "Laptop Lenovo ThinkPad E14",
        "category": "Laptops",
        "brand": "Lenovo",
        "cost_price": 2450,
        "sale_price": 3290,
        "attributes": [("Color", "Negro"), ("Garantía", "1 año")],
        "short_description": "Laptop empresarial de 14 pulgadas con procesador Intel i5.",
    },
    {
        "name": "Impresora Epson EcoTank L3250",
        "category": "Impresoras",
        "brand": "Epson",
        "cost_price": 780,
        "sale_price": 999,
        "attributes": [("Color", "Negro"), ("Garantía", "1 año")],
        "short_description": "Impresora multifuncional con sistema de tinta continua.",
    },
    {
        "name": "Monitor Samsung 24\" IPS",
        "category": "Monitores",
        "brand": "Samsung",
        "cost_price": 480,
        "sale_price": 649,
        "attributes": [("Garantía", "1 año")],
        "short_description": "Monitor Full HD de 24 pulgadas con panel IPS.",
    },
    {
        "name": "Router TP-Link Archer AX55",
        "category": "Routers",
        "brand": "TP-Link",
        "cost_price": 290,
        "sale_price": 399,
        "attributes": [("Color", "Negro"), ("Garantía", "1 año")],
        "short_description": "Router WiFi 6 de doble banda AX3000.",
    },
    {
        "name": "Celular Xiaomi Redmi Note 13",
        "category": "Celulares",
        "brand": "Xiaomi",
        "cost_price": 620,
        "sale_price": 849,
        "attributes": [("Color", "Azul"), ("Garantía", "1 año")],
        "short_description": "Smartphone con pantalla AMOLED y 128GB de almacenamiento.",
    },
    {
        "name": "SSD Kingston 1TB NV2",
        "category": "Discos SSD",
        "brand": "Kingston",
        "cost_price": 210,
        "sale_price": 299,
        "attributes": [("Capacidad", "1TB"), ("Garantía", "2 años")],
        "short_description": "Unidad de estado sólido NVMe PCIe 4.0.",
    },
    {
        "name": "Servicio de Instalación de Cámara",
        "category": "Servicios de Instalación",
        "brand": None,
        "cost_price": 0,
        "sale_price": 120,
        "attributes": [("Garantía", "6 meses")],
        "short_description": "Instalación profesional de cámaras de seguridad.",
        "is_serialized": False,
    },
    {
        "name": "Taza de Sublimación 11oz",
        "category": "Tazas de Sublimación",
        "brand": None,
        "cost_price": 6.5,
        "sale_price": 15,
        "attributes": [("Color", "Blanco")],
        "short_description": "Taza blanca de cerámica para sublimación, 11oz.",
    },
]


async def _get_or_create_brand(db: AsyncSession, name: str) -> Brand:
    existing = (
        await db.execute(select(Brand).where(Brand.name == name))
    ).scalar_one_or_none()
    if existing:
        return existing
    brand = Brand(name=name, slug=slugify(name))
    db.add(brand)
    await db.flush()
    return brand


async def _get_or_create_category(
    db: AsyncSession, name: str, parent_slug: str | None
) -> Category:
    existing = (
        await db.execute(select(Category).where(Category.slug == slugify(name)))
    ).scalar_one_or_none()
    if existing:
        return existing
    parent = None
    if parent_slug:
        parent = (
            await db.execute(
                select(Category).where(Category.slug == slugify(parent_slug))
            )
        ).scalar_one_or_none()
    category = Category(
        name=name, slug=slugify(name), parent_id=parent.id if parent else None
    )
    db.add(category)
    await db.flush()
    return category


async def seed_exchange_rate(db: AsyncSession) -> int:
    """Inserta el tipo de cambio de hoy (idempotente)."""
    now = datetime.now(UTC)
    from datetime import timedelta

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    existing = (
        await db.execute(
            select(ExchangeRate)
            .where(
                ExchangeRate.currency_from == "USD",
                ExchangeRate.currency_to == "PEN",
                ExchangeRate.effective_at >= day_start,
                ExchangeRate.effective_at < day_end,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing:
        return 0
    db.add(
        ExchangeRate(
            currency_from="USD",
            currency_to="PEN",
            rate=3.75,
            source="seed",
            effective_at=now,
        )
    )
    await db.flush()
    return 1


async def seed_catalog(db: AsyncSession) -> dict[str, int]:
    """Siembra catálogo de forma idempotente. Retorna conteos creados."""
    counts = {"brands": 0, "categories": 0, "attributes": 0, "products": 0}

    owner = (
        await db.execute(select(User).where(User.email == "owner@hasbun.dev"))
    ).scalar_one_or_none()
    if owner is None:
        raise RuntimeError("Seed de usuarios debe ejecutarse antes del catálogo (owner@hasbun.dev)")

    for name in BRANDS:
        if (
            await db.execute(select(Brand).where(Brand.name == name))
        ).scalar_one_or_none():
            continue
        await _get_or_create_brand(db, name)
        counts["brands"] += 1

    for name, parent in CATEGORIES:
        if (
            await db.execute(select(Category).where(Category.slug == slugify(name)))
        ).scalar_one_or_none():
            continue
        await _get_or_create_category(db, name, parent)
        counts["categories"] += 1

    attribute_values: dict[str, uuid.UUID] = {}
    for name, (data_type, values) in ATTRIBUTES.items():
        existing = (
            await db.execute(select(Attribute).where(Attribute.name == name))
        ).scalar_one_or_none()
        if existing is None:
            attribute = await create_attribute(
                db,
                data=type("_", (), {"name": name, "data_type": data_type, "unit": None})(),
                created_by=owner,
            )
            counts["attributes"] += 1
        else:
            attribute = existing
        for value in values:
            from app.modules.products.domain.models import AttributeValue

            av = (
                await db.execute(
                    select(AttributeValue).where(
                        AttributeValue.attribute_id == attribute.id,
                        AttributeValue.value == value,
                    )
                )
            ).scalar_one_or_none()
            if av is None:
                await add_attribute_value(
                    db, attribute_id=attribute.id, value=value, created_by=owner
                )
        attribute_values[name] = attribute.id

    for product_data in PRODUCTS:
        from app.modules.products.domain.models import Product

        existing_product = (
            await db.execute(select(Product).where(Product.name == product_data["name"]))
        ).scalar_one_or_none()
        if existing_product:
            continue

        brand = None
        if product_data.get("brand"):
            brand = await _get_or_create_brand(db, product_data["brand"])
        category = await _get_or_create_category(
            db, product_data["category"], None
        )

        attributes_input = [
            ProductAttributeInput(attribute_id=attribute_values[attr_name], value=value)
            for attr_name, value in product_data.get("attributes", [])
        ]
        await create_product(
            db,
            data=ProductCreate(
                name=product_data["name"],
                cost_price=product_data["cost_price"],
                sale_price=product_data["sale_price"],
                brand_id=brand.id if brand else None,
                category_id=category.id,
                short_description=product_data.get("short_description"),
                is_serialized=product_data.get("is_serialized", False),
                price_rule=PriceRule.FIXED_PEN,
                currency="PEN",
                attributes=attributes_input,
            ),
            created_by=owner,
        )
        counts["products"] += 1

    await db.commit()
    return counts

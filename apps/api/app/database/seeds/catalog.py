"""Seeds de catálogo: marcas, categorías, atributos y productos ficticios (#F02-12)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attributes.domain.models import Attribute, AttributeValue
from app.modules.brands.domain.models import Brand
from app.modules.categories.domain.models import Category
from app.modules.products.domain.models import Product, ProductOffer, SerializedUnit
from app.modules.products.infrastructure.sku import generate_sku, seed_sku_prefixes

# --- Marcas ---
BRANDS: list[tuple[str, str]] = [
    ("HP", "hp"),
    ("Lenovo", "lenovo"),
    ("Samsung", "samsung"),
    ("Canon", "canon"),
    ("Epson", "epson"),
    ("Hikvision", "hikvision"),
    ("LG", "lg"),
]

# --- Categorías (nombre, slug, slug_padre) ---
CATEGORIES: list[tuple[str, str, str | None]] = [
    ("Electrodomésticos", "electrodomesticos", None),
    ("Televisores", "televisores", "electrodomesticos"),
    ("Cómputo", "computo", None),
    ("Laptops", "laptops", "computo"),
    ("Laptops HP", "laptops-hp", "laptops"),
    ("Computadoras", "computadoras", "computo"),
    ("Impresoras", "impresoras", "computo"),
    ("Accesorios", "accesorios", "computo"),
    ("Seguridad Electrónica", "seguridad", None),
    ("Cámaras", "camaras", "seguridad"),
    ("Monitores", "monitores", "computo"),
    ("Almacenamiento", "almacenamiento", "computo"),
]

# --- Atributos del sistema (nombre, data_type, unit) ---
ATTRIBUTES: list[tuple[str, str, str | None]] = [
    ("RAM", "text", "GB"),
    ("SSD", "text", "GB"),
    ("CPU", "text", None),
    ("Pantalla", "text", "pulgadas"),
    ("Color", "text", None),
    ("Capacidad", "text", "GB"),
    ("Resolución", "text", None),
    ("Modelo", "text", None),
    ("Voltaje", "number", "V"),
    ("Tipo de cámara", "list", None),
    ("Megapíxeles", "number", "MP"),
]

ATTR_VALUES: dict[str, list[str]] = {
    "RAM": ["4GB", "8GB", "16GB", "32GB"],
    "SSD": ["256GB", "512GB", "1TB"],
    "CPU": ["Intel Core i3", "Intel Core i5", "Intel Core i7", "AMD Ryzen 5", "AMD Ryzen 7"],
    "Pantalla": ['14"', '15.6"', '17"', '21.5"', '27"', '32"', '55"', '65"'],
    "Color": ["Negro", "Plateado", "Blanco", "Gris"],
    "Tipo de cámara": ["IP", "Analógica", "PTZ", "Bullet", "Domo"],
}

# --- Productos: (nombre, slug_categoria, slug_marca, costo, precio, moneda,
#     regla, serializado, atributos, publicado, stock_min)
_PRODUCTS: list[dict[str, Any]] = [
    {
        "name": "Laptop HP 15s-FQ5003 Intel Core i5 8GB",
        "category": "laptops-hp",
        "brand": "hp",
        "cost_price": Decimal("1850.00"),
        "sale_price": Decimal("2199.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 2,
        "attributes": {
            "RAM": "8GB",
            "SSD": "512GB",
            "CPU": "Intel Core i5",
            "Pantalla": '15.6"',
            "Color": "Negro",
        },
    },
    {
        "name": "Laptop Lenovo IdeaPad 3 Core i7 16GB",
        "category": "laptops",
        "brand": "lenovo",
        "cost_price": Decimal("2800.00"),
        "sale_price": Decimal("3299.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 1,
        "attributes": {
            "RAM": "16GB",
            "SSD": "512GB",
            "CPU": "Intel Core i7",
            "Pantalla": '15.6"',
            "Color": "Gris",
        },
    },
    {
        "name": "Laptop HP Core i3 8GB para oficina",
        "category": "laptops-hp",
        "brand": "hp",
        "cost_price": Decimal("1200.00"),
        "sale_price": Decimal("1499.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 3,
        "attributes": {
            "RAM": "8GB",
            "SSD": "256GB",
            "CPU": "Intel Core i3",
            "Pantalla": '14"',
            "Color": "Negro",
        },
    },
    {
        "name": "Laptop Samsung Galaxy Book 16GB",
        "category": "laptops",
        "brand": "samsung",
        "cost_price": Decimal("3400.00"),
        "sale_price": Decimal("3999.00"),
        "currency": "USD",
        "price_rule": "USD_CONVERTED",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 1,
        "attributes": {"RAM": "16GB", "SSD": "1TB", "Pantalla": '15.6"', "Color": "Plateado"},
    },
    {
        "name": "Laptop gamer Lenovo Legion Ryzen 7",
        "category": "laptops",
        "brand": "lenovo",
        "cost_price": Decimal("4200.00"),
        "sale_price": Decimal("4899.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 1,
        "attributes": {
            "RAM": "32GB",
            "SSD": "1TB",
            "CPU": "AMD Ryzen 7",
            "Pantalla": '17"',
            "Color": "Negro",
        },
    },
    {
        "name": "Computadora de escritorio HP 8GB 512GB",
        "category": "computadoras",
        "brand": "hp",
        "cost_price": Decimal("1600.00"),
        "sale_price": Decimal("1999.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 2,
        "attributes": {"RAM": "8GB", "SSD": "512GB", "CPU": "Intel Core i5", "Color": "Negro"},
    },
    {
        "name": "Computadora de escritorio DIY Ryzen 5",
        "category": "computadoras",
        "brand": "lenovo",
        "cost_price": Decimal("1400.00"),
        "sale_price": Decimal("1799.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 2,
        "attributes": {"RAM": "16GB", "SSD": "512GB", "CPU": "AMD Ryzen 5", "Color": "Negro"},
    },
    {
        "name": "Computadora de escritorio HP Core i3 4GB",
        "category": "computadoras",
        "brand": "hp",
        "cost_price": Decimal("900.00"),
        "sale_price": Decimal("1099.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": False,
        "stock_minimum": 2,
        "attributes": {"RAM": "4GB", "SSD": "256GB", "CPU": "Intel Core i3", "Color": "Negro"},
    },
    {
        "name": "Impresora multifuncional Epson L3250",
        "category": "impresoras",
        "brand": "epson",
        "cost_price": Decimal("480.00"),
        "sale_price": Decimal("599.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 3,
        "attributes": {"Modelo": "L3250", "Color": "Negro"},
    },
    {
        "name": "Impresora láser HP LaserJet M111a",
        "category": "impresoras",
        "brand": "hp",
        "cost_price": Decimal("650.00"),
        "sale_price": Decimal("799.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 2,
        "attributes": {"Modelo": "M111a", "Color": "Blanco"},
    },
    {
        "name": "Impresora Epson EcoTank L4260",
        "category": "impresoras",
        "brand": "epson",
        "cost_price": Decimal("750.00"),
        "sale_price": Decimal("899.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 2,
        "attributes": {"Modelo": "L4260"},
    },
    {
        "name": "Teclado mecánico retroiluminado",
        "category": "accesorios",
        "brand": "hp",
        "cost_price": Decimal("45.00"),
        "sale_price": Decimal("79.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 5,
        "attributes": {"Color": "Negro"},
    },
    {
        "name": "Mouse inalámbrico logitec negro",
        "category": "accesorios",
        "brand": "hp",
        "cost_price": Decimal("25.00"),
        "sale_price": Decimal("49.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 10,
        "attributes": {"Color": "Negro"},
    },
    {
        "name": "Cable HDMI 2.0 2m",
        "category": "accesorios",
        "brand": "samsung",
        "cost_price": Decimal("12.00"),
        "sale_price": Decimal("29.90"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 15,
        "attributes": {"Color": "Negro"},
    },
    {
        "name": "Parlante bluetooth Samsung",
        "category": "accesorios",
        "brand": "samsung",
        "cost_price": Decimal("90.00"),
        "sale_price": Decimal("149.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": True,
        "stock_minimum": 4,
        "attributes": {"Color": "Negro"},
    },
    {
        "name": "Pasta térmica Arctic MX-4",
        "category": "accesorios",
        "brand": "epson",
        "cost_price": Decimal("15.00"),
        "sale_price": Decimal("35.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": False,
        "published": False,
        "stock_minimum": 8,
        "attributes": {},
    },
    {
        "name": "Cámara IP Hikvision 2MP Bullet",
        "category": "camaras",
        "brand": "hikvision",
        "cost_price": Decimal("130.00"),
        "sale_price": Decimal("189.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 5,
        "attributes": {"Tipo de cámara": "IP", "Megapíxeles": "2", "Resolución": "1080p"},
    },
    {
        "name": "Cámara IP Hikvision 4MP Domo",
        "category": "camaras",
        "brand": "hikvision",
        "cost_price": Decimal("160.00"),
        "sale_price": Decimal("229.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 4,
        "attributes": {"Tipo de cámara": "IP", "Megapíxeles": "4", "Resolución": "2K"},
    },
    {
        "name": "Cámara PTZ Hikvision 5MP",
        "category": "camaras",
        "brand": "hikvision",
        "cost_price": Decimal("450.00"),
        "sale_price": Decimal("599.00"),
        "currency": "USD",
        "price_rule": "USD_CONVERTED",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 1,
        "attributes": {"Tipo de cámara": "PTZ", "Megapíxeles": "5"},
    },
    {
        "name": "Televisor LED Samsung 55\" 4K",
        "category": "televisores",
        "brand": "samsung",
        "cost_price": Decimal("1550.00"),
        "sale_price": Decimal("1899.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 2,
        "attributes": {"Pantalla": '55"', "Resolución": "4K UHD"},
    },
    {
        "name": "Televisor LED LG 65\" 4K Smart",
        "category": "televisores",
        "brand": "lg",
        "cost_price": Decimal("2400.00"),
        "sale_price": Decimal("2899.00"),
        "currency": "PEN",
        "price_rule": "MANUAL",
        "is_serialized": True,
        "published": True,
        "stock_minimum": 1,
        "attributes": {"Pantalla": '65"', "Resolución": "4K UHD"},
    },
]

# Seriales para productos serializados
SERIALS: dict[str, list[tuple[str, str, str | None, str | None, str | None]]] = {
    "Laptop HP 15s-FQ5003 Intel Core i5 8GB": [
        ("HP15S-FQ5003-001", "AVAILABLE", None, None, None),
        ("HP15S-FQ5003-002", "AVAILABLE", None, None, None),
    ],
    "Cámara IP Hikvision 2MP Bullet": [
        ("HIK-BULLET-2MP-001", "AVAILABLE", None, None, "00:1A:2B:3C:4D:01"),
        ("HIK-BULLET-2MP-002", "RESERVED", None, None, "00:1A:2B:3C:4D:02"),
    ],
    "Televisor LED Samsung 55\" 4K": [
        ("SAMSUNG-55UHD-001", "AVAILABLE", None, None, None),
    ],
}


async def seed_brands(db: AsyncSession) -> int:
    created = 0
    for name, slug in BRANDS:
        exists = (await db.execute(select(Brand).where(Brand.slug == slug))).scalars().first()
        if exists is None:
            db.add(Brand(name=name, slug=slug, active=True))
            created += 1
    await db.commit()
    return created


async def seed_categories(db: AsyncSession) -> int:
    created = 0
    for name, slug, parent_slug in CATEGORIES:
        exists = (await db.execute(select(Category).where(Category.slug == slug))).scalars().first()
        if exists is not None:
            continue
        parent = None
        if parent_slug:
            row = await db.execute(
                select(Category).where(Category.slug == parent_slug)
            )
            parent = row.scalars().first()
        db.add(Category(name=name, slug=slug, parent_id=parent.id if parent else None, active=True))
        created += 1
    await db.commit()
    return created


async def seed_attributes(db: AsyncSession) -> int:
    created = 0
    for name, data_type, unit in ATTRIBUTES:
        exists = (
            await db.execute(select(Attribute).where(Attribute.name == name))
        ).scalars().first()
        if exists is None:
            db.add(Attribute(name=name, data_type=data_type, unit=unit))
            created += 1
    await db.commit()

    # Valores comunes
    values_created = 0
    for attr_name, values in ATTR_VALUES.items():
        attr = (
            await db.execute(select(Attribute).where(Attribute.name == attr_name))
        ).scalars().first()
        if attr is None:
            continue
        existing = set(
            (
                await db.execute(
                    select(AttributeValue.value).where(
                        AttributeValue.attribute_id == attr.id
                    )
                )
            ).scalars().all()
        )
        for value in values:
            if value not in existing:
                db.add(AttributeValue(attribute_id=attr.id, value=value))
                values_created += 1
    await db.commit()
    return {"attributes_created": created, "values_created": values_created}  # type: ignore[return-value]


async def _resolve_attr_value(db: AsyncSession, name: str, value: str) -> AttributeValue | None:
    result = await db.execute(
        select(AttributeValue)
        .join(Attribute, Attribute.id == AttributeValue.attribute_id)
        .where(Attribute.name == name, AttributeValue.value == value)
    )
    return result.scalars().first()


async def seed_products(db: AsyncSession) -> dict[str, int]:
    """Siembra productos ficticios de forma idempotente (por slug de nombre)."""
    await seed_sku_prefixes(db)
    categories = {
        c.slug: c for c in (await db.execute(select(Category))).scalars().all()
    }
    brands = {b.slug: b for b in (await db.execute(select(Brand))).scalars().all()}

    existing_names = set((await db.execute(select(Product.name))).scalars().all())
    serials_by_product: dict[str, Product] = {}
    created = 0

    for spec in _PRODUCTS:
        name = spec["name"]
        if name in existing_names:
            continue
        category = categories.get(str(spec["category"]))
        brand = brands.get(str(spec["brand"]))
        prefix = None
        if category:
            from app.modules.products.infrastructure.sku import prefix_for_category

            prefix = prefix_for_category(category.slug)

        product = Product(
            sku=await generate_sku(db, prefix or "PRD"),
            name=name,
            slug=None,
            brand_id=brand.id if brand else None,
            category_id=category.id if category else None,
            cost_price=spec["cost_price"],  # type: ignore[arg-type]
            sale_price=spec["sale_price"],  # type: ignore[arg-type]
            currency=spec["currency"],  # type: ignore[arg-type]
            price_rule=spec["price_rule"],  # type: ignore[arg-type]
            active=True,
            published=bool(spec["published"]),
            stock_minimum=int(spec["stock_minimum"]),
            is_serialized=bool(spec["is_serialized"]),
        )
        # slug único
        from app.modules.products.infrastructure.sku import prefix_for_category as _p  # noqa: F401

        base_slug = name.lower().replace(" ", "-").replace('"', "").replace("\\", "")
        import re

        base_slug = re.sub(r"[^a-z0-9-]", "", base_slug)
        product.slug = base_slug
        db.add(product)
        await db.flush()
        serials_by_product[name] = product
        created += 1

        # Atributos dinámicos
        for attr_name, value in spec["attributes"].items():  # type: ignore[union-attr]
            av = await _resolve_attr_value(db, attr_name, str(value))
            if av is None:
                attr = (
                    await db.execute(select(Attribute).where(Attribute.name == attr_name))
                ).scalars().first()
                if attr is None:
                    attr = Attribute(name=attr_name, data_type="text")
                    db.add(attr)
                    await db.flush()
                av = AttributeValue(attribute_id=attr.id, value=str(value))
                db.add(av)
                await db.flush()
            from app.modules.attributes.domain.models import ProductAttributeValue

            db.add(ProductAttributeValue(product_id=product.id, attribute_value_id=av.id))

    await db.commit()
    return {"products_created": created}


async def seed_serials_and_offers(db: AsyncSession) -> int:
    """Registra seriales y ofertas vigentes para algunos productos (#F02-12)."""
    await seed_sku_prefixes(db)
    now = datetime.now(UTC)
    extra = 0

    for product_name, serials in SERIALS.items():
        product = (
            await db.execute(select(Product).where(Product.name == product_name))
        ).scalars().first()
        if product is None:
            continue
        existing = set(
            (
                await db.execute(
                    select(SerializedUnit.serial_number).where(
                        SerializedUnit.product_id == product.id
                    )
                )
            ).scalars().all()
        )
        for serial_number, status, imei, imei2, mac in serials:
            if serial_number in existing:
                continue
            db.add(
                SerializedUnit(
                    product_id=product.id,
                    serial_number=serial_number,
                    imei=imei,
                    imei2=imei2,
                    mac_address=mac,
                    status=status,
                )
            )
            extra += 1

    # Ofertas activas (productos publicados con precio alto)
    offer_targets: list[tuple[str, Decimal, Decimal]] = [
        ("Laptop HP 15s-FQ5003 Intel Core i5 8GB", Decimal("2199.00"), Decimal("1999.00")),
        ("Televisor LED LG 65\" 4K Smart", Decimal("2899.00"), Decimal("2599.00")),
        ("Impresora multifuncional Epson L3250", Decimal("599.00"), Decimal("549.00")),
    ]
    for product_name, normal, offer in offer_targets:
        product = (
            await db.execute(select(Product).where(Product.name == product_name))
        ).scalars().first()
        if product is None:
            continue
        exists = (
            await db.execute(
                select(ProductOffer).where(ProductOffer.product_id == product.id)
            )
        ).scalars().first()
        if exists is None:
            db.add(
                ProductOffer(
                    product_id=product.id,
                    normal_price=normal,
                    offer_price=offer,
                    start_at=now - timedelta(days=1),
                    end_at=now + timedelta(days=15),
                    active=True,
                )
            )
            extra += 1

    await db.commit()
    return extra


async def seed_catalog(db: AsyncSession) -> dict[str, object]:
    brands = await seed_brands(db)
    categories = await seed_categories(db)
    attributes = await seed_attributes(db)
    products = await seed_products(db)
    serials = await seed_serials_and_offers(db)
    return {
        "brands_created": brands,
        "categories_created": categories,
        "attributes": attributes,
        **products,
        "serials_and_offers_created": serials,
    }

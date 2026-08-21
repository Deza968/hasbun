"""Seeds de inventario inicial: proveedores y compras ficticias (#F03-11, #F03-18).

Al ejecutarse, los productos del seed de FASE 02 quedan con stock > 0 y
coherente (calculado por movimientos PURCHASE, nunca por campo).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.models import InventoryMovement, MovementType
from app.modules.products.domain.models import Product, SerializedUnit
from app.modules.purchases.domain.models import (
    Purchase,
    PurchaseItem,
    PurchaseStatus,
)
from app.modules.purchases.infrastructure.code import next_purchase_code
from app.modules.suppliers.domain.models import Supplier
from app.modules.users.domain.models import User

# (razon_social, ruc, nombre_comercial, contacto, telefono, whatsapp, email, ciudad)
SUPPLIERS: list[tuple[str, str, str, str, str, str, str, str]] = [
    (
        "TecnoImport Perú S.A.C.",
        "20123456789",
        "TecnoImport",
        "Carlos Ramírez",
        "01 456 7890",
        "+51998765432",
        "ventas@tecnoimport.pe",
        "Lima",
    ),
    (
        "Distribuidora Electronorte E.I.R.L.",
        "20456789012",
        "Electronorte",
        "María Torres",
        "044 223344",
        "+51976543210",
        "maria@electronorte.pe",
        "Trujillo",
    ),
    (
        "Importaciones Hikvis Perú",
        "20567890123",
        "Hikvis Perú",
        "Jorge Vega",
        "01 612 3456",
        "+51965432109",
        "jorge@hikvisperu.com",
        "Lima",
    ),
    (
        "Suministros Gamer Store S.A.C.",
        "20678901234",
        "Gamer Store",
        "Lucía Paredes",
        "01 278 9012",
        "+51954321098",
        "compras@gamerstore.pe",
        "Arequipa",
    ),
    (
        "Perú Electrohogar S.A.",
        "20789012345",
        "Electrohogar",
        "Pedro Salazar",
        "01 345 6789",
        "+51943210987",
        "pedro@electrohogar.pe",
        "Lima",
    ),
]

# (producto, proveedor_idx, cantidad, costo_unitario, moneda, seriales_por_unidad)
# cantidad y seriales solo si es serializado: se crean seriales ficticios.
PURCHASE_SEEDS: list[tuple[str, int, Decimal, Decimal, str]] = [
    ("Laptop HP 15s-FQ5003 Intel Core i5 8GB", 0, Decimal("10"), Decimal("1850.00"), "PEN"),
    ("Laptop Lenovo IdeaPad 3 Core i7 16GB", 3, Decimal("5"), Decimal("2800.00"), "PEN"),
    ("Laptop HP Core i3 8GB para oficina", 0, Decimal("8"), Decimal("1200.00"), "PEN"),
    ("Laptop Samsung Galaxy Book 16GB", 1, Decimal("4"), Decimal("920.00"), "USD"),
    ("Laptop gamer Lenovo Legion Ryzen 7", 3, Decimal("3"), Decimal("4200.00"), "PEN"),
    ("Computadora de escritorio HP 8GB 512GB", 0, Decimal("6"), Decimal("1600.00"), "PEN"),
    ("Computadora de escritorio DIY Ryzen 5", 4, Decimal("6"), Decimal("1400.00"), "PEN"),
    ("Computadora de escritorio HP Core i3 4GB", 4, Decimal("5"), Decimal("900.00"), "PEN"),
    ("Impresora multifuncional Epson L3250", 1, Decimal("12"), Decimal("480.00"), "PEN"),
    ("Impresora láser HP LaserJet M111a", 0, Decimal("8"), Decimal("650.00"), "PEN"),
    ("Impresora Epson EcoTank L4260", 1, Decimal("6"), Decimal("750.00"), "PEN"),
    ("Teclado mecánico retroiluminado", 3, Decimal("25"), Decimal("45.00"), "PEN"),
    ("Mouse inalámbrico logitec negro", 3, Decimal("40"), Decimal("25.00"), "PEN"),
    ("Cable HDMI 2.0 2m", 3, Decimal("60"), Decimal("12.00"), "PEN"),
    ("Parlante bluetooth Samsung", 4, Decimal("15"), Decimal("90.00"), "PEN"),
    ("Pasta térmica Arctic MX-4", 1, Decimal("20"), Decimal("15.00"), "PEN"),
    ("Cámara IP Hikvision 2MP Bullet", 2, Decimal("18"), Decimal("130.00"), "PEN"),
    ("Cámara IP Hikvision 4MP Domo", 2, Decimal("12"), Decimal("160.00"), "PEN"),
    ("Cámara PTZ Hikvision 5MP", 2, Decimal("4"), Decimal("125.00"), "USD"),
    ("Televisor LED Samsung 55\" 4K", 4, Decimal("6"), Decimal("1550.00"), "PEN"),
    ("Televisor LED LG 65\" 4K Smart", 4, Decimal("3"), Decimal("2400.00"), "PEN"),
]

DEFAULT_RATE = Decimal("3.75")


async def seed_suppliers(db: AsyncSession) -> int:
    created = 0
    for razon, ruc, nombre, contacto, tel, wa, email, ciudad in SUPPLIERS:
        exists = (
            await db.execute(select(Supplier).where(Supplier.ruc == ruc))
        ).scalars().first()
        if exists is None:
            db.add(
                Supplier(
                    razon_social=razon,
                    ruc=ruc,
                    nombre_comercial=nombre,
                    contacto_nombre=contacto,
                    telefono=tel,
                    telefono_whatsapp=wa,
                    email=email,
                    ciudad=ciudad,
                    active=True,
                )
            )
            created += 1
    await db.commit()
    return created


async def _resolve_owner(db: AsyncSession) -> User:
    owner = (
        await db.execute(select(User).where(User.email == "owner@hasbun.dev"))
    ).scalars().first()
    return owner


async def seed_purchases(db: AsyncSession) -> dict[str, int]:
    """Crea compras RECEIVED que generan los movimientos de stock inicial."""
    owner = await _resolve_owner(db)
    if owner is None:
        return {"purchases_created": 0, "serials_created": 0}

    suppliers = {s.razon_social: s for s in (await db.execute(select(Supplier))).scalars().all()}
    purchases_created = 0
    serials_created = 0
    now = datetime.now(UTC)

    for product_name, supplier_idx, qty, unit_cost, currency in PURCHASE_SEEDS:
        product = (
            await db.execute(select(Product).where(Product.name == product_name))
        ).scalars().first()
        supplier_razon = SUPPLIERS[supplier_idx][0]
        supplier = suppliers.get(supplier_razon)
        if product is None or supplier is None:
            continue

        # Verificar si el producto ya tiene stock de seed.
        has_movement = (
            await db.execute(
                select(InventoryMovement.id).where(
                    InventoryMovement.product_id == product.id
                ).limit(1)
            )
        ).scalars().first()
        if has_movement is not None:
            continue

        price = unit_cost
        if currency == "USD" and product.currency == "PEN":
            price = (unit_cost * DEFAULT_RATE).quantize(Decimal("0.01"))

        purchase = Purchase(
            code=await next_purchase_code(db),
            supplier_id=supplier.id,
            status=PurchaseStatus.RECEIVED,
            total=(qty * price).quantize(Decimal("0.01")),
            currency=currency,
            exchange_rate=DEFAULT_RATE if currency == "USD" else Decimal("1"),
            exchange_rate_source="seed",
            received_at=now - timedelta(days=30),
            created_by=owner.id,
        )
        db.add(purchase)
        await db.flush()

        item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=qty,
            unit_cost=price,
            subtotal=(qty * price).quantize(Decimal("0.01")),
            received_quantity=qty,
        )
        db.add(item)
        await db.flush()

        db.add(
            InventoryMovement(
                product_id=product.id,
                quantity=qty,
                movement_type=MovementType.PURCHASE,
                reference_type="purchase",
                reference_id=purchase.id,
                warehouse="principal",
                unit_cost=price,
                notes="Compra inicial (seed FASE 03)",
                created_by=owner.id,
            )
        )
        purchases_created += 1

        # Seriales ficticios para productos serializados (#F03-18).
        if product.is_serialized:
            existing_serials = set(
                (
                    await db.execute(
                        select(SerializedUnit.serial_number).where(
                            SerializedUnit.product_id == product.id
                        )
                    )
                ).scalars().all()
            )
            base = f"{product.sku}-SER"
            for i in range(int(qty)):
                serial = f"{base}-{i + 1:03d}"
                if serial in existing_serials:
                    continue
                db.add(
                    SerializedUnit(
                        product_id=product.id,
                        serial_number=serial,
                        status="AVAILABLE",
                        purchase_item_id=item.id,
                    )
                )
                serials_created += 1

    await db.commit()
    return {"purchases_created": purchases_created, "serials_created": serials_created}


async def seed_inventory(db: AsyncSession) -> dict[str, int]:
    suppliers = await seed_suppliers(db)
    purchases = await seed_purchases(db)
    return {"suppliers_created": suppliers, **purchases}

"""Seeds de ventas ficticias CASH - F04-14.

Crea 10 ventas CASH con items aleatorios usando productos con stock.
Usa CashSession activa o crea una. Idempotente: no duplica si ya hay >=10 ventas.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.cash.domain.models import CashMovement, CashRegister, CashSession
from app.modules.customers.domain.models import Customer
from app.modules.inventory.domain.models import InventoryMovement, MovementType
from app.modules.inventory.infrastructure.repository import get_stock_summary
from app.modules.products.domain.models import Product, SerializedUnit
from app.modules.sales.domain.models import Sale, SaleItem, SalePayment
from app.modules.sales.infrastructure.code import next_sale_code
from app.modules.users.domain.models import User

TARGET_SALES = 10


async def _get_or_create_session(db: AsyncSession, user: User) -> CashSession | None:
    """Retorna sesión OPEN del usuario o crea una nueva en su caja asignada."""
    result = await db.execute(select(CashSession).where(CashSession.user_id == user.id, CashSession.status == "OPEN"))
    session = result.scalars().first()
    if session is not None:
        return session

    # Buscar caja asignada al usuario o fallback a Caja Ventas / Caja General
    register = (
        await db.execute(select(CashRegister).where(CashRegister.user_id == user.id, CashRegister.active.is_(True)))
    ).scalars().first()
    if register is None:
        register = (await db.execute(select(CashRegister).where(CashRegister.name == "Caja Ventas"))).scalars().first()
    if register is None:
        register = (await db.execute(select(CashRegister).where(CashRegister.active.is_(True)))).scalars().first()
    if register is None:
        return None

    now = datetime.now(UTC)
    session = CashSession(
        register_id=register.id,
        user_id=user.id,
        status="OPEN",
        opening_amount=Decimal("200.00"),
        expected_cash=Decimal("0.00"),
        counted_cash=Decimal("0.00"),
        difference=Decimal("0.00"),
        opened_at=now,
        opened_by=user.id,
    )
    db.add(session)
    await db.flush()

    # Movimiento OPENING (opcional, solo si amount>0)
    opening = CashMovement(
        session_id=session.id,
        type="OPENING",
        amount=Decimal("200.00"),
        direction="IN",
        reason="Apertura seed F04-14",
        created_by=user.id,
    )
    db.add(opening)
    await db.flush()
    return session


async def seed_sales(db: AsyncSession) -> dict[str, int]:
    """Crea 10 ventas ficticias CASH idempotentes.

    - Usa productos con stock disponible (>0).
    - Si no hay stock o no hay sesión/caja, salta ese item/venta.
    - Usa DocumentSequence vía next_sale_code.
    - Crea Sale + SaleItem + SalePayment + InventoryMovement + CashMovement.
    - Idempotente: si ya hay >=10 ventas no crea más (completa hasta 10).
    """
    total_existing = (await db.execute(select(func.count(Sale.id)))).scalar() or 0
    if total_existing >= TARGET_SALES:
        return {"sales_created": 0, "sales_total": int(total_existing), "sales_skipped": 1}

    need = TARGET_SALES - int(total_existing)

    # Resolver usuario ventas (fallback owner)
    ventas_user = (await db.execute(select(User).where(User.email == "ventas@hasbun.dev"))).scalars().first()
    if ventas_user is None:
        ventas_user = (await db.execute(select(User).where(User.email == "owner@hasbun.dev"))).scalars().first()
    if ventas_user is None:
        return {"sales_created": 0, "sales_total": int(total_existing), "error": 1}

    session = await _get_or_create_session(db, ventas_user)
    if session is None:
        return {"sales_created": 0, "sales_total": int(total_existing), "error": 1}

    # Productos candidatos con stock >0 (se calcula una vez, luego se revalida por item)
    products: list[Product] = (await db.execute(select(Product).where(Product.active.is_(True)))).scalars().all()
    # Mezclar para aleatoriedad determinística por seed
    random.shuffle(products)

    # Filtrar productos con stock disponible
    available_products: list[Product] = []
    for p in products:
        summary = await get_stock_summary(db, p.id)
        if summary.available > 0:
            available_products.append(p)

    if not available_products:
        return {"sales_created": 0, "sales_total": int(total_existing), "no_stock": 1}

    customers: list[Customer] = (await db.execute(select(Customer))).scalars().all()

    created = 0
    # Guardar productos disponibles para re-evaluar stock en cada venta
    # Usar copia mutable del stock visto para no sobre-vender en el mismo seed run
    # (revalidamos con get_stock_summary antes de cada item)

    random.seed(42)

    for _ in range(need):
        # Si nos quedamos sin productos con stock, detener
        if not available_products:
            break

        # Elegir 1-3 productos aleatorios distintos
        n_items = random.randint(1, min(3, len(available_products)))  # noqa: S311
        chosen = random.sample(available_products, k=n_items)  # noqa: S311

        sale_items_data: list[dict] = []
        subtotal = Decimal("0.00")

        for product in chosen:
            summary = await get_stock_summary(db, product.id)
            if summary.available <= 0:
                continue

            qty = Decimal(str(random.randint(1, min(2, int(summary.available)))))  # noqa: S311
            if qty <= 0:
                continue

            # Manejo serializado: requiere unidad AVAILABLE
            serialized_unit_id = None
            if product.is_serialized:
                # Forzar qty=1 para serializados
                qty = Decimal("1")
                if summary.available < 1:
                    continue
                unit_row = (
                    await db.execute(
                        select(SerializedUnit).where(
                            SerializedUnit.product_id == product.id,
                            SerializedUnit.status == "AVAILABLE",
                        )
                    )
                ).scalars().first()
                if unit_row is None:
                    continue
                serialized_unit_id = unit_row.id
                # Marcar como SOLD (se hará commit al final)
                unit_row.status = "SOLD"

            # Precio vigente con oferta si aplica
            unit_price = product.sale_price
            now = datetime.now(UTC)
            for offer in product.offers:
                if offer.active and offer.start_at <= now <= offer.end_at:
                    unit_price = offer.offer_price
                    break

            item_sub = (unit_price * qty).quantize(Decimal("0.01"))
            subtotal += item_sub
            sale_items_data.append(
                {
                    "product": product,
                    "serialized_unit_id": serialized_unit_id,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "unit_cost": product.cost_price,
                    "subtotal": item_sub,
                }
            )

        if not sale_items_data:
            continue

        subtotal = subtotal.quantize(Decimal("0.01"))
        total = subtotal

        # Cliente aleatorio (opcional)
        customer_id = random.choice(customers).id if customers else None  # noqa: S311

        exchange_rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))
        code = await next_sale_code(db)

        sale = Sale(
            code=code,
            customer_id=customer_id,
            sale_type="CASH",
            status="PAID",
            subtotal=subtotal,
            discount_amount=Decimal("0.00"),
            total=total,
            currency="PEN",
            exchange_rate=exchange_rate,
            exchange_rate_source="mock",
            exchange_rate_timestamp=datetime.now(UTC),
            cash_session_id=session.id,
            idempotency_key=f"seed-sale-{code}",
            notes="Venta seed F04-14",
            created_by=ventas_user.id,
        )
        db.add(sale)
        await db.flush()

        for item in sale_items_data:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item["product"].id,
                serialized_unit_id=item["serialized_unit_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                unit_cost=item["unit_cost"],
                discount_amount=Decimal("0.00"),
                subtotal=item["subtotal"],
            )
            db.add(sale_item)

            # Movimiento inventario
            db.add(
                InventoryMovement(
                    product_id=item["product"].id,
                    quantity=-item["quantity"],
                    movement_type=MovementType.SALE,
                    reference_type="sale",
                    reference_id=sale.id,
                    warehouse="principal",
                    unit_cost=item["unit_cost"],
                    notes="Venta seed F04-14",
                    created_by=ventas_user.id,
                )
            )

        # Pago único en efectivo
        db.add(
            SalePayment(
                sale_id=sale.id,
                method="CASH",
                amount=total,
                reference=None,
                idempotency_key=f"seed-pay-{code}",
                paid_at=datetime.now(UTC),
                registered_by=ventas_user.id,
            )
        )

        # Movimiento caja
        db.add(
            CashMovement(
                session_id=session.id,
                type="SALE_INCOME",
                amount=total,
                direction="IN",
                reference_type="sale",
                reference_id=sale.id,
                created_by=ventas_user.id,
                idempotency_key=f"seed-cash-{code}",
            )
        )

        await db.flush()
        created += 1

    if created:
        await db.commit()
    else:
        # Si se marcó algún SerializedUnit como SOLD y no se creó venta, hacer rollback
        # pero ya flusheamos cambios de serial; si created==0 y hubo serial touch sin venta,
        # el rollback no es necesario porque no hubo ventas reales; commitear el estado de seriales
        # solo si cambió (en este branch no se creó venta completa, evitar commit innecesario)
        await db.rollback()

    final_total = (await db.execute(select(func.count(Sale.id)))).scalar() or 0
    return {"sales_created": created, "sales_total": int(final_total)}

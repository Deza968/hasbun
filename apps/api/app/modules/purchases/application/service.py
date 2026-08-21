"""Servicio de compras: creación, confirmación y recepción (#F03-09).

La recepción de una compra es una operación ATÓMICA que genera los
movimientos de inventario (PURCHASE, +qty) y actualiza seriales.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.modules.audit.application.service import log
from app.modules.inventory.application.service import register_purchase
from app.modules.products.domain.models import Product
from app.modules.purchases.domain.models import (
    Purchase,
    PurchaseItem,
    PurchaseStatus,
)
from app.modules.purchases.infrastructure import repository
from app.modules.purchases.infrastructure.code import next_purchase_code
from app.modules.suppliers.domain.models import Supplier
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def _compute_total(items: list[PurchaseItem]) -> Decimal:
    total = Decimal("0")
    for item in items:
        item.subtotal = (item.quantity * item.unit_cost).quantize(Decimal("0.01"))
        total += item.subtotal
    return total.quantize(Decimal("0.01"))


async def create_purchase(
    db: AsyncSession, *, data, created_by: User
) -> Purchase:
    supplier = await db.get(Supplier, data.supplier_id)
    if supplier is None:
        raise NotFoundError("Proveedor no encontrado")
    if not supplier.active:
        raise ValidationError("El proveedor está inactivo")
    if not data.items:
        raise ValidationError("La compra debe tener al menos un ítem")

    for item in data.items:
        product = await db.get(Product, item.product_id)
        if product is None:
            raise NotFoundError("Producto no encontrado")

    purchase = Purchase(
        code=await next_purchase_code(db),
        supplier_id=data.supplier_id,
        status=PurchaseStatus.DRAFT,
        total=Decimal("0"),
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        exchange_rate_source=data.exchange_rate_source,
        notes=data.notes,
        created_by=created_by.id,
    )
    db.add(purchase)
    await db.flush()

    items: list[PurchaseItem] = []
    for item in data.items:
        product = await db.get(Product, item.product_id)
        if product is None:
            raise NotFoundError("Producto no encontrado")
        price = item.unit_cost
        # Si la compra es en USD y el producto está en PEN, el costo se
        # almacena en la moneda del producto (regla de negocio simple).
        if data.currency == "USD" and product.currency == "PEN":
            price = (item.unit_cost * data.exchange_rate).quantize(Decimal("0.01"))
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_cost=price,
            subtotal=(item.quantity * price).quantize(Decimal("0.01")),
            received_quantity=Decimal("0"),
            notes=item.notes,
        )
        purchase_item.product = product  # puebla la relación para la respuesta
        db.add(purchase_item)
        items.append(purchase_item)

    purchase.total = await _compute_total(items)
    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="CREATE_PURCHASE",
        module="purchases",
        user_id=created_by.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={"code": purchase.code, "total": str(purchase.total)},
    )
    return purchase


async def update_purchase(
    db: AsyncSession, *, purchase_id: uuid.UUID, data, user: User
) -> Purchase:
    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    if purchase.status != PurchaseStatus.DRAFT:
        raise BusinessRuleError("Solo se puede editar una compra en estado borrador")

    if data.supplier_id is not None:
        supplier = await db.get(Supplier, data.supplier_id)
        if supplier is None:
            raise NotFoundError("Proveedor no encontrado")
        purchase.supplier_id = data.supplier_id
    for field in ("currency", "exchange_rate", "exchange_rate_source", "notes"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(purchase, field, value)

    if data.items is not None:
        for old_item in list(purchase.items):
            await db.delete(old_item)
        await db.flush()
        items: list[PurchaseItem] = []
        for item in data.items:
            product = await db.get(Product, item.product_id)
            if product is None:
                raise NotFoundError("Producto no encontrado")
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                subtotal=(item.quantity * item.unit_cost).quantize(Decimal("0.01")),
                received_quantity=Decimal("0"),
                notes=item.notes,
            )
            purchase_item.product = product
            db.add(purchase_item)
            items.append(purchase_item)
        purchase.total = await _compute_total(items)

    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="UPDATE_PURCHASE",
        module="purchases",
        user_id=user.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={"status": purchase.status},
    )
    return purchase


async def confirm_order(db: AsyncSession, *, purchase_id: uuid.UUID, user: User) -> Purchase:
    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    if purchase.status != PurchaseStatus.DRAFT:
        raise BusinessRuleError("Solo se puede confirmar un borrador")
    purchase.status = PurchaseStatus.ORDERED
    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="CONFIRM_PURCHASE",
        module="purchases",
        user_id=user.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={"status": PurchaseStatus.ORDERED},
    )
    return purchase


async def receive_purchase(
    db: AsyncSession, *, purchase_id: uuid.UUID, received_items: list[dict], user: User
) -> Purchase:
    """Recepción atómica de compra: actualiza ítems y genera movimientos.

    [TRANSACCIÓN]: si algo falla, el rollback deshace movimientos e ítems.
    """
    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    if purchase.status in {PurchaseStatus.RECEIVED, PurchaseStatus.CANCELLED}:
        raise ConflictError("La compra ya fue recibida o cancelada")

    received_map = {r["item_id"]: r["received_quantity"] for r in received_items}
    all_received = True
    total_received = Decimal("0")

    for item in purchase.items:
        if item.id not in received_map:
            raise ValidationError(
                f"Debe indicar la cantidad recibida para el ítem {item.id}"
            )
        qty = received_map[item.id]
        if qty < 0 or qty > item.quantity:
            raise ValidationError(
                f"Cantidad recibida inválida para el producto "
                f"{item.product.name}: máx {item.quantity}"
            )
        item.received_quantity = qty
        total_received += (qty * item.unit_cost).quantize(Decimal("0.01"))
        if qty < item.quantity:
            all_received = False
        if qty > 0:
            # Movimiento de inventario PURCHASE (+qty) — mismo transaction.
            await register_purchase(
                db,
                product_id=item.product_id,
                qty=qty,
                reference_id=purchase.id,
                created_by=user.id,
                unit_cost=item.unit_cost,
            )
            # Si es serializado, crear SerializedUnit por unidad (#F03-18).
            product = await db.get(Product, item.product_id)
            if product is not None and product.is_serialized:
                from app.modules.products.domain.models import SerializedUnit

                # serial_numbers opcional; si no viene se autogenera.
                serials_input = next(
                    (
                        r.get("serial_numbers")
                        for r in received_items
                        if r.get("item_id") == str(item.id)
                    ),
                    None,
                )
                for i in range(int(qty)):
                    if serials_input and i < len(serials_input):
                        serial = serials_input[i]
                    else:
                        # Generación determinística: SKU + timestamp corto
                        serial = f"{product.sku}-SER-{purchase.code}-{i+1:03d}"
                    db.add(
                        SerializedUnit(
                            product_id=item.product_id,
                            serial_number=serial,
                            status="AVAILABLE",
                            purchase_item_id=item.id,
                        )
                    )

    purchase.status = PurchaseStatus.RECEIVED if all_received else PurchaseStatus.PARTIAL
    purchase.received_at = datetime.now(UTC)

    # Actualizar costo de los productos recibidos (costo promedio simple).
    for item in purchase.items:
        if item.received_quantity > 0:
            product = await db.get(Product, item.product_id)
            if product is not None:
                product.cost_price = item.unit_cost

    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="RECEIVE_PURCHASE",
        module="purchases",
        user_id=user.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={
            "status": purchase.status,
            "received_at": purchase.received_at.isoformat() if purchase.received_at else None,
            "total_received": str(total_received),
        },
    )
    return purchase


async def cancel_purchase(
    db: AsyncSession, *, purchase_id: uuid.UUID, reason: str, user: User
) -> Purchase:
    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    if purchase.status == PurchaseStatus.RECEIVED:
        raise ConflictError("No se puede cancelar una compra ya recibida")
    if purchase.status == PurchaseStatus.CANCELLED:
        raise ValidationError("La compra ya está cancelada")
    purchase.status = PurchaseStatus.CANCELLED
    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="CANCEL_PURCHASE",
        module="purchases",
        user_id=user.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={"status": PurchaseStatus.CANCELLED, "reason": reason},
    )
    return purchase


async def upload_invoice(
    db: AsyncSession, *, purchase_id: uuid.UUID, file_id: uuid.UUID, user: User
) -> Purchase:
    from app.modules.files.domain.models import FileObject

    purchase = await repository.get_by_id(db, purchase_id)
    if purchase is None:
        raise NotFoundError("Compra no encontrada")
    file = await db.get(FileObject, file_id)
    if file is None:
        raise NotFoundError("Archivo no encontrado")
    purchase.invoice_file_id = file_id
    await db.commit()
    purchase = await repository.get_by_id(db, purchase.id)
    await log(
        action="UPLOAD_PURCHASE_INVOICE",
        module="purchases",
        user_id=user.id,
        entity_type="Purchase",
        entity_id=purchase.id,
        new_values={"invoice_file_id": str(file_id)},
    )
    return purchase

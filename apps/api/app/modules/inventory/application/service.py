"""Servicio de inventario con control de concurrencia (#F03-03).

Todas las operaciones que mutan inventario adquieren un lock de fila sobre
el producto (`SELECT ... FOR UPDATE`) para serializar accesos concurrentes,
y verifican el stock disponible antes de crear el movimiento.

Los movimientos son INMUTABLES: este servicio solo INSERTA.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core.exceptions import InsufficientStockError, NotFoundError, ValidationError
from app.modules.audit.domain.models import AuditLog
from app.modules.inventory.domain.models import InventoryMovement, MovementType
from app.modules.inventory.infrastructure import repository
from app.modules.products.domain.models import Product
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _lock_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    """Bloquea la fila del producto para serializar operaciones concurrentes."""
    product = (
        await db.execute(
            select(Product).where(Product.id == product_id).with_for_update()
        )
    ).scalar_one_or_none()
    if product is None:
        raise NotFoundError("Producto no encontrado")
    return product


async def reserve_stock(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    qty: Decimal,
    reference_type: str,
    reference_id: uuid.UUID,
    created_by: uuid.UUID | None,
) -> InventoryMovement:
    """Reserva stock. Lanza `InsufficientStockError` si no hay disponible (#F03-03)."""
    await _lock_product(db, product_id)
    summary = await repository.get_stock_summary(db, product_id)
    if summary.available < qty:
        raise InsufficientStockError(
            f"Stock insuficiente: disponible {summary.available}, requerido {qty}"
        )
    return await repository.add_movement(
        db,
        product_id=product_id,
        quantity=-qty,
        movement_type=MovementType.RESERVATION,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
        notes=f"Reserva {reference_type}",
    )


async def release_reservation(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    qty: Decimal,
    reference_id: uuid.UUID,
    created_by: uuid.UUID | None,
) -> InventoryMovement:
    """Libera una reserva previa (#F03-03)."""
    await _lock_product(db, product_id)
    return await repository.add_movement(
        db,
        product_id=product_id,
        quantity=qty,
        movement_type=MovementType.RELEASE_RESERVATION,
        reference_type="sale",
        reference_id=reference_id,
        created_by=created_by,
        notes="Liberación de reserva",
    )


async def confirm_sale(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    qty: Decimal,
    reference_id: uuid.UUID,
    created_by: uuid.UUID | None,
    unit_cost: Decimal | None = None,
) -> InventoryMovement:
    """Confirma una venta: movimiento SALE (-qty). Verifica disponibilidad (#F03-03)."""
    await _lock_product(db, product_id)
    summary = await repository.get_stock_summary(db, product_id)
    if summary.available < qty:
        raise InsufficientStockError(
            f"Stock insuficiente: disponible {summary.available}, requerido {qty}"
        )
    return await repository.add_movement(
        db,
        product_id=product_id,
        quantity=-qty,
        movement_type=MovementType.SALE,
        reference_type="sale",
        reference_id=reference_id,
        unit_cost=unit_cost,
        created_by=created_by,
        notes="Venta confirmada",
    )


async def register_purchase(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    qty: Decimal,
    reference_id: uuid.UUID,
    created_by: uuid.UUID | None,
    unit_cost: Decimal | None = None,
) -> InventoryMovement:
    """Registra ingreso de stock por compra recibida (PURCHASE, +qty) (#F03-09)."""
    await _lock_product(db, product_id)
    return await repository.add_movement(
        db,
        product_id=product_id,
        quantity=qty,
        movement_type=MovementType.PURCHASE,
        reference_type="purchase",
        reference_id=reference_id,
        unit_cost=unit_cost,
        created_by=created_by,
        notes="Recepción de compra",
    )


async def register_adjustment(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    qty: Decimal,
    reason: str,
    authorized_by: uuid.UUID,
    notes: str | None = None,
) -> InventoryMovement:
    """Registra un ajuste manual autorizado (ADJUSTMENT_IN/OUT) (#F03-05).

    Requiere autorización de OWNER (verificado por el router). Crea un
    AuditLog y lo referencia como `authorization_id` del movimiento.
    """
    if qty == 0:
        raise ValidationError("La cantidad del ajuste no puede ser cero")
    if not reason.strip():
        raise ValidationError("El motivo del ajuste es obligatorio")

    await _lock_product(db, product_id)
    before = await repository.get_stock_summary(db, product_id)

    if qty > 0:
        movement_type = MovementType.ADJUSTMENT_IN
    else:
        if before.available < abs(qty):
            raise InsufficientStockError(
                f"Stock insuficiente para ajustar: disponible {before.available}"
            )
        movement_type = MovementType.ADJUSTMENT_OUT

    # Auditoría obligatoria con stock antes/después (misma transacción).
    after_available = before.available + qty
    audit = AuditLog(
        user_id=authorized_by,
        action="ADJUST_INVENTORY",
        module="inventory",
        entity_type="Product",
        entity_id=product_id,
        old_values={"available": str(before.available)},
        new_values={
            "available": str(after_available),
            "qty": str(qty),
            "reason": reason,
        },
    )
    db.add(audit)
    await db.flush()

    return await repository.add_movement(
        db,
        product_id=product_id,
        quantity=qty,
        movement_type=movement_type,
        reference_type="adjustment",
        reference_id=audit.id,
        created_by=authorized_by,
        authorization_id=audit.id,
        notes=notes or reason,
    )


async def list_kardex(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    movement_type: str | None = None,
    date_from=None,
    date_to=None,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, object]:
    """Devuelve el kardex con saldo acumulado por línea (#F03-04)."""
    product = await db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    items, total, final_balance = await repository.list_movements(
        db,
        product_id=product_id,
        movement_type=movement_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return {
        "product_id": product_id,
        "product_name": product.name,
        "sku": product.sku,
        "items": items,
        "total": total,
        "final_balance": final_balance,
    }

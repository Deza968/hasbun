"""Repositorio de inventario (#F03-02, #F03-04).

Los movimientos son INMUTABLES: no existen métodos update/delete.
El stock se calcula SIEMPRE sumando movimientos, nunca leyendo un campo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.inventory.application.schemas import StockResponse
from app.modules.inventory.domain.models import InventoryMovement, MovementType
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class StockSummary:
    """Resumen de stock de un producto.

    - `physical`: stock físico en almacén (entradas - salidas físicas).
    - `reserved`: unidades comprometidas por reserva.
    - `partially_paid`: unidades separadas por apartado.
    - `on_credit`: unidades entregadas a crédito.
    - `available`: disponible para comprometer (physical - comprometido).
    - `total_physical`: alias de `physical`.
    """

    available: Decimal
    reserved: Decimal
    partially_paid: Decimal
    on_credit: Decimal
    total_physical: Decimal

    @property
    def low_stock(self) -> bool:
        return self.available <= 0

    @classmethod
    def empty(cls) -> StockSummary:
        zero = Decimal("0")
        return cls(
            available=zero,
            reserved=zero,
            partially_paid=zero,
            on_credit=zero,
            total_physical=zero,
        )


def _movement_sign_expression():
    """Expresión CASE: 1 para tipos físicos (el signo ya está en `quantity`).

    `quantity` es firmado: positivo = entrada, negativo = salida.
    """
    return case(
        (
            InventoryMovement.movement_type.in_(
                MovementType.PHYSICAL_IN | MovementType.PHYSICAL_OUT
            ),
            1,
        ),
        else_=0,
    )


async def get_stock_summary(
    db: AsyncSession, product_id: uuid.UUID
) -> StockSummary:
    """Calcula el stock en una sola query agregada (#F03-02)."""
    row = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(
                        _movement_sign_expression() * InventoryMovement.quantity
                    ),
                    0,
                ).label("physical"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                InventoryMovement.movement_type.in_(MovementType.RESERVATIONS),
                                -InventoryMovement.quantity,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("reserved"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                InventoryMovement.movement_type.in_(MovementType.PARTIAL_HOLDS),
                                -InventoryMovement.quantity,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("partially_paid"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                InventoryMovement.movement_type.in_(MovementType.CREDITS),
                                -InventoryMovement.quantity,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("on_credit"),
            ).where(InventoryMovement.product_id == product_id)
        )
    ).one()
    physical = Decimal(row.physical)
    reserved = Decimal(row.reserved)
    partially_paid = Decimal(row.partially_paid)
    on_credit = Decimal(row.on_credit)
    return StockSummary(
        available=physical - reserved - partially_paid - on_credit,
        reserved=reserved,
        partially_paid=partially_paid,
        on_credit=on_credit,
        total_physical=physical,
    )


async def list_movements(
    db: AsyncSession,
    *,
    product_id: uuid.UUID,
    movement_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[InventoryMovement], int, Decimal]:
    """Lista movimientos de un producto en orden cronológico (#F03-04)."""
    query = select(InventoryMovement).where(InventoryMovement.product_id == product_id)
    count_query = select(func.count(InventoryMovement.id)).where(
        InventoryMovement.product_id == product_id
    )

    if movement_type:
        query = query.where(InventoryMovement.movement_type == movement_type)
        count_query = count_query.where(InventoryMovement.movement_type == movement_type)
    if date_from:
        query = query.where(InventoryMovement.created_at >= date_from)
        count_query = count_query.where(InventoryMovement.created_at >= date_from)
    if date_to:
        query = query.where(InventoryMovement.created_at <= date_to)
        count_query = count_query.where(InventoryMovement.created_at <= date_to)

    total = (await db.execute(count_query)).scalar()
    query = (
        query.order_by(InventoryMovement.created_at.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = (await db.execute(query)).scalars().unique().all()

    # Saldo físico acumulado al momento de cada movimiento (para el kardex).
    # `quantity` es firmado: positivo = entrada, negativo = salida.
    running_balance = Decimal("0")
    balances: list[Decimal] = []
    for item in items:
        if item.movement_type in MovementType.PHYSICAL_IN | MovementType.PHYSICAL_OUT:
            running_balance += item.quantity
        balances.append(running_balance)

    return list(items), int(total or 0), running_balance


async def sum_movements(
    db: AsyncSession, product_id: uuid.UUID
) -> Decimal:
    """Suma algebraica total de movimientos (para locks y verificación)."""
    value = (
        await db.execute(
            select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
                InventoryMovement.product_id == product_id
            )
        )
    ).scalar()
    return Decimal(value)


async def add_movement(db: AsyncSession, **fields) -> InventoryMovement:
    """Inserta un movimiento. Es la ÚNICA vía de escritura del repositorio."""
    movement = InventoryMovement(**fields)
    db.add(movement)
    await db.flush()
    return movement


async def list_stock(
    db: AsyncSession, *, page: int = 1, per_page: int = 20
) -> tuple[list[StockResponse], int]:
    """Lista stock de todos los productos usando la vista `v_product_stock`.

    La vista precalcula por producto; aquí solo se pagina y se castean
    valores a Decimal (nunca float).
    """
    total = (
        await db.execute(text("SELECT count(*) FROM v_product_stock_summary"))
    ).scalar()
    rows = (
        await db.execute(
            text(
                "SELECT product_id, sku, product_name, available, reserved, "
                "partially_paid, on_credit, total_physical, stock_minimum "
                "FROM v_product_stock_summary "
                "ORDER BY product_name "
                "LIMIT :limit OFFSET :offset"
            ),
            {"limit": per_page, "offset": (page - 1) * per_page},
        )
    ).all()
    items = [
        StockResponse(
            product_id=row.product_id,
            sku=row.sku,
            product_name=row.product_name,
            available=Decimal(str(row.available)),
            reserved=Decimal(str(row.reserved)),
            partially_paid=Decimal(str(row.partially_paid)),
            on_credit=Decimal(str(row.on_credit)),
            total_physical=Decimal(str(row.total_physical)),
            low_stock=Decimal(str(row.available)) <= Decimal(str(row.stock_minimum or 0)),
            stock_minimum=int(row.stock_minimum or 0),
        )
        for row in rows
    ]
    return items, int(total or 0)

"""Modelo del módulo de inventario (#F03-01).

El stock NUNCA es un campo editable: es la suma algebraica de los
movimientos. `InventoryMovement` es INMUTABLE: no existe UPDATE ni DELETE.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.products.domain.models import Product
    from app.modules.users.domain.models import User


class MovementType:
    """Tipos de movimiento de inventario (#F03-01)."""

    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RESERVATION = "RESERVATION"
    RELEASE_RESERVATION = "RELEASE_RESERVATION"
    PARTIAL_PAYMENT_HOLD = "PARTIAL_PAYMENT_HOLD"
    CREDIT_DELIVERY = "CREDIT_DELIVERY"
    SALE_COMPLETED = "SALE_COMPLETED"
    RETURN = "RETURN"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    REPAIR_USAGE = "REPAIR_USAGE"
    REPAIR_RETURN = "REPAIR_RETURN"
    DAMAGED = "DAMAGED"
    TRANSFER = "TRANSFER"

    ALL = {
        PURCHASE,
        SALE,
        RESERVATION,
        RELEASE_RESERVATION,
        PARTIAL_PAYMENT_HOLD,
        CREDIT_DELIVERY,
        SALE_COMPLETED,
        RETURN,
        ADJUSTMENT_IN,
        ADJUSTMENT_OUT,
        REPAIR_USAGE,
        REPAIR_RETURN,
        DAMAGED,
        TRANSFER,
    }

    # Tipos que suman al stock físico en almacén
    PHYSICAL_IN = {PURCHASE, ADJUSTMENT_IN, RETURN, REPAIR_RETURN}
    PHYSICAL_OUT = {SALE, ADJUSTMENT_OUT, REPAIR_USAGE, DAMAGED}
    # Tipos de compromiso (reserva / hold / crédito)
    RESERVATIONS = {RESERVATION, RELEASE_RESERVATION}
    PARTIAL_HOLDS = {PARTIAL_PAYMENT_HOLD}
    CREDITS = {CREDIT_DELIVERY, SALE_COMPLETED}
    # Los ajustes requieren autorización (FK → AuditLog)
    ADJUSTMENTS = {ADJUSTMENT_IN, ADJUSTMENT_OUT}


class InventoryMovement(BaseModel, Base):
    """Movimiento de inventario. Registro inmutable (#F03-01)."""

    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index(
            "ix_inventory_movements_product_created",
            "product_id",
            text("created_at DESC"),
        ),
        Index(
            "ix_inventory_movements_reference",
            "reference_type",
            "reference_id",
        ),
        Index(
            "ix_inventory_movements_type_created",
            "movement_type",
            "created_at",
        ),
        CheckConstraint(
            "movement_type IN ('ADJUSTMENT_IN','ADJUSTMENT_OUT') = (authorization_id IS NOT NULL)",
            name="adjustment_requires_auth",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    serialized_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False
    )  # + entrada, - salida
    movement_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    reference_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # sale / purchase / repair / adjustment / transfer
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    warehouse: Mapped[str] = mapped_column(
        String(50), nullable=False, default="principal"
    )
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    authorization_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )  # AuditLog para ADJUSTMENT_*

    product: Mapped[Product] = relationship("Product", lazy="selectin")
    creator: Mapped[User | None] = relationship("User", lazy="selectin")

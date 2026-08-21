"""FASE 03 - inventario y compras: suppliers, purchases, purchase_items,
inventory_movements, purchase_sequences, vista v_product_stock

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-20 14:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Proveedores (#F03-07) ---
    op.create_table(
        "suppliers",
        sa.Column("razon_social", sa.String(length=255), nullable=False),
        sa.Column("ruc", sa.String(length=11), nullable=True),
        sa.Column("nombre_comercial", sa.String(length=255), nullable=True),
        sa.Column("contacto_nombre", sa.String(length=255), nullable=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("telefono_whatsapp", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("ciudad", sa.String(length=120), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_suppliers_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suppliers")),
        sa.UniqueConstraint("ruc", name=op.f("uq_suppliers_ruc")),
    )
    op.create_index(op.f("ix_suppliers_razon_social"), "suppliers", ["razon_social"], unique=False)

    # --- Secuencia de códigos de compra (#F03-09) ---
    op.create_table(
        "purchase_sequences",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("last_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("year", name=op.f("pk_purchase_sequences")),
    )

    # --- Compras (#F03-08) ---
    op.create_table(
        "purchases",
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("supplier_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(10, 4), nullable=False),
        sa.Column("exchange_rate_source", sa.String(length=50), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_file_id", sa.UUID(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_purchases_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_file_id"], ["file_objects.id"], name=op.f("fk_purchases_invoice_file_id_file_objects"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], name=op.f("fk_purchases_supplier_id_suppliers"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_purchases")),
    )
    op.create_index(op.f("ix_purchases_code"), "purchases", ["code"], unique=True)
    op.create_index(op.f("ix_purchases_supplier_id"), "purchases", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_purchases_status"), "purchases", ["status"], unique=False)
    op.create_table(
        "purchase_items",
        sa.Column("purchase_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_purchase_items_quantity_positive")),
        sa.CheckConstraint("unit_cost >= 0", name=op.f("ck_purchase_items_unit_cost_non_negative")),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_purchase_items_product_id_products"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], name=op.f("fk_purchase_items_purchase_id_purchases"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_purchase_items")),
    )
    op.create_index(op.f("ix_purchase_items_product_id"), "purchase_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_purchase_items_purchase_id"), "purchase_items", ["purchase_id"], unique=False)

    # --- Movimientos de inventario (#F03-01) ---
    op.create_table(
        "inventory_movements",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("serialized_unit_id", sa.UUID(), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("reference_type", sa.String(length=30), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("warehouse", sa.String(length=50), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("authorization_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "movement_type IN ('ADJUSTMENT_IN','ADJUSTMENT_OUT') = (authorization_id IS NOT NULL)",
            name=op.f("ck_inventory_movements_adjustment_requires_auth"),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_inventory_movements_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_inventory_movements_product_id_products"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_movements")),
    )
    op.create_index(
        op.f("ix_inventory_movements_product_id"),
        "inventory_movements",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_product_created",
        "inventory_movements",
        ["product_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_reference",
        "inventory_movements",
        ["reference_type", "reference_id"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_movements_type_created",
        "inventory_movements",
        ["movement_type", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_inventory_movements_movement_type"), "inventory_movements", ["movement_type"], unique=False)

    # --- Vista de stock precalculado (#F03-02) ---
    # `quantity` es firmado: positivo = entrada, negativo = salida.
    op.execute(
        """
        CREATE OR REPLACE VIEW v_product_stock AS
        SELECT
            p.id AS product_id,
            p.sku,
            p.name AS product_name,
            p.stock_minimum,
            p.is_serialized,
            p.active,
            p.published,
            COALESCE(
                SUM(
                    CASE
                        WHEN m.movement_type IN ('PURCHASE','ADJUSTMENT_IN','RETURN','REPAIR_RETURN',
                                                 'SALE','ADJUSTMENT_OUT','REPAIR_USAGE','DAMAGED')
                        THEN m.quantity
                        ELSE 0
                    END
                ), 0
            ) AS physical,
            COALESCE(
                -SUM(CASE WHEN m.movement_type IN ('RESERVATION','RELEASE_RESERVATION') THEN m.quantity ELSE 0 END), 0
            ) AS reserved,
            COALESCE(
                -SUM(CASE WHEN m.movement_type = 'PARTIAL_PAYMENT_HOLD' THEN m.quantity ELSE 0 END), 0
            ) AS partially_paid,
            COALESCE(
                -SUM(CASE WHEN m.movement_type IN ('CREDIT_DELIVERY','SALE_COMPLETED') THEN m.quantity ELSE 0 END), 0
            ) AS on_credit,
            COALESCE(
                SUM(
                    CASE
                        WHEN m.movement_type IN ('PURCHASE','ADJUSTMENT_IN','RETURN','REPAIR_RETURN',
                                                 'SALE','ADJUSTMENT_OUT','REPAIR_USAGE','DAMAGED')
                        THEN m.quantity
                        ELSE 0
                    END
                ), 0
            ) - COALESCE(
                -SUM(CASE WHEN m.movement_type IN ('RESERVATION','RELEASE_RESERVATION') THEN m.quantity ELSE 0 END), 0
            ) - COALESCE(
                -SUM(CASE WHEN m.movement_type = 'PARTIAL_PAYMENT_HOLD' THEN m.quantity ELSE 0 END), 0
            ) - COALESCE(
                -SUM(CASE WHEN m.movement_type IN ('CREDIT_DELIVERY','SALE_COMPLETED') THEN m.quantity ELSE 0 END), 0
            ) AS available
        FROM products p
        LEFT JOIN inventory_movements m ON m.product_id = p.id
        GROUP BY p.id
        """
    )
    # Vista auxiliar con total físico (alias legible para reportes).
    op.execute(
        """
        CREATE OR REPLACE VIEW v_product_stock_summary AS
        SELECT
            product_id,
            sku,
            product_name,
            stock_minimum,
            is_serialized,
            active,
            published,
            physical,
            reserved,
            partially_paid,
            on_credit,
            available,
            physical AS total_physical
        FROM v_product_stock
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_product_stock_summary")
    op.execute("DROP VIEW IF EXISTS v_product_stock")
    op.drop_index(op.f("ix_inventory_movements_movement_type"), table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_type_created", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_reference", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_product_created", table_name="inventory_movements")
    op.drop_index(op.f("ix_inventory_movements_product_id"), table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index(op.f("ix_purchase_items_purchase_id"), table_name="purchase_items")
    op.drop_index(op.f("ix_purchase_items_product_id"), table_name="purchase_items")
    op.drop_table("purchase_items")
    op.drop_index(op.f("ix_purchases_status"), table_name="purchases")
    op.drop_index(op.f("ix_purchases_supplier_id"), table_name="purchases")
    op.drop_index(op.f("ix_purchases_code"), table_name="purchases")
    op.drop_table("purchases")
    op.drop_table("purchase_sequences")
    op.drop_index(op.f("ix_suppliers_razon_social"), table_name="suppliers")
    op.drop_table("suppliers")
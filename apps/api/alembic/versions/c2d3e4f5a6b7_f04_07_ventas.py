"""F04-07 ventas

Revision ID: c2d3e4f5a6b7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa

revision = "c2d3e4f5a6b7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("document_sequences", sa.Column("prefix", sa.String(10), nullable=False), sa.Column("year", sa.Integer(), nullable=False), sa.Column("last_value", sa.Integer(), nullable=False), sa.PrimaryKeyConstraint("prefix", "year", name=op.f("pk_document_sequences")))
    op.create_table("discount_authorizations", sa.Column("sale_id", sa.UUID(), nullable=True), sa.Column("type", sa.String(20), nullable=False), sa.Column("percentage", sa.Numeric(5,4), nullable=True), sa.Column("fixed_amount", sa.Numeric(14,2), nullable=True), sa.Column("reason", sa.Text(), nullable=False), sa.Column("requested_by", sa.UUID(), nullable=False), sa.Column("approved_by", sa.UUID(), nullable=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False), sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("percentage >= 0 AND percentage <= 1", name=op.f("ck_discount_authorizations_percentage_range")), sa.CheckConstraint("fixed_amount >= 0", name=op.f("ck_discount_authorizations_fixed_amount_positive")), sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name=op.f("fk_discount_authorizations_approved_by_users"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["requested_by"], ["users.id"], name=op.f("fk_discount_authorizations_requested_by_users"), ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id", name=op.f("pk_discount_authorizations")))
    op.create_index(op.f("ix_discount_authorizations_status"), "discount_authorizations", ["status"], unique=False)
    op.create_table("sales", sa.Column("code", sa.String(20), nullable=False), sa.Column("customer_id", sa.UUID(), nullable=True), sa.Column("sale_type", sa.String(20), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("subtotal", sa.Numeric(14,2), nullable=False), sa.Column("discount_amount", sa.Numeric(14,2), nullable=False), sa.Column("total", sa.Numeric(14,2), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("exchange_rate", sa.Numeric(10,4), nullable=False), sa.Column("exchange_rate_source", sa.String(50), nullable=True), sa.Column("exchange_rate_timestamp", sa.DateTime(timezone=True), nullable=True), sa.Column("discount_authorization_id", sa.UUID(), nullable=True), sa.Column("cash_session_id", sa.UUID(), nullable=True), sa.Column("idempotency_key", sa.String(80), nullable=True), sa.Column("notes", sa.Text(), nullable=True), sa.Column("created_by", sa.UUID(), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("total >= 0", name=op.f("ck_sales_total_non_negative")), sa.CheckConstraint("discount_amount >= 0", name=op.f("ck_sales_discount_non_negative")), sa.ForeignKeyConstraint(["cash_session_id"], ["cash_sessions.id"], name=op.f("fk_sales_cash_session_id_cash_sessions"), ondelete="RESTRICT"), sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_sales_created_by_users"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name=op.f("fk_sales_customer_id_customers"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["discount_authorization_id"], ["discount_authorizations.id"], name=op.f("fk_sales_discount_authorization_id_discount_authorizations"), ondelete="SET NULL"), sa.PrimaryKeyConstraint("id", name=op.f("pk_sales")))
    op.create_index(op.f("ix_sales_code"), "sales", ["code"], unique=True)
    op.create_index(op.f("ix_sales_idempotency_key"), "sales", ["idempotency_key"], unique=True)
    op.create_index(op.f("ix_sales_status"), "sales", ["status"], unique=False)
    op.create_table("sale_items", sa.Column("sale_id", sa.UUID(), nullable=False), sa.Column("product_id", sa.UUID(), nullable=False), sa.Column("serialized_unit_id", sa.UUID(), nullable=True), sa.Column("quantity", sa.Numeric(14,3), nullable=False), sa.Column("unit_price", sa.Numeric(14,2), nullable=False), sa.Column("unit_cost", sa.Numeric(14,2), nullable=False), sa.Column("discount_amount", sa.Numeric(14,2), nullable=False), sa.Column("subtotal", sa.Numeric(14,2), nullable=False), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("quantity > 0", name=op.f("ck_sale_items_quantity_positive")), sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_sale_items_product_id_products"), ondelete="RESTRICT"), sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], name=op.f("fk_sale_items_sale_id_sales"), ondelete="CASCADE"), sa.ForeignKeyConstraint(["serialized_unit_id"], ["serialized_units.id"], name=op.f("fk_sale_items_serialized_unit_id_serialized_units"), ondelete="SET NULL"), sa.PrimaryKeyConstraint("id", name=op.f("pk_sale_items")))
    op.create_index(op.f("ix_sale_items_sale_id"), "sale_items", ["sale_id"], unique=False)
    op.create_table("sale_payments", sa.Column("sale_id", sa.UUID(), nullable=False), sa.Column("method", sa.String(30), nullable=False), sa.Column("method_detail", sa.String(120), nullable=True), sa.Column("amount", sa.Numeric(14,2), nullable=False), sa.Column("reference", sa.String(100), nullable=True), sa.Column("idempotency_key", sa.String(80), nullable=True), sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False), sa.Column("registered_by", sa.UUID(), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["registered_by"], ["users.id"], name=op.f("fk_sale_payments_registered_by_users"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], name=op.f("fk_sale_payments_sale_id_sales"), ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name=op.f("pk_sale_payments")), sa.UniqueConstraint("idempotency_key", name=op.f("uq_sale_payments_idempotency_key")))
    op.create_index(op.f("ix_sale_payments_sale_id"), "sale_payments", ["sale_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_sale_payments_sale_id"), table_name="sale_payments")
    op.drop_table("sale_payments")
    op.drop_index(op.f("ix_sale_items_sale_id"), table_name="sale_items")
    op.drop_table("sale_items")
    op.drop_index(op.f("ix_sales_status"), table_name="sales")
    op.drop_index(op.f("ix_sales_idempotency_key"), table_name="sales")
    op.drop_index(op.f("ix_sales_code"), table_name="sales")
    op.drop_table("sales")
    op.drop_index(op.f("ix_discount_authorizations_status"), table_name="discount_authorizations")
    op.drop_table("discount_authorizations")
    op.drop_table("document_sequences")

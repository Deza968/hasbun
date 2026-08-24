"""F06 cotizaciones whatsapp notificaciones

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    # --- quotes (#F06-01) ---
    op.create_table("quotes", sa.Column("code", sa.String(20), nullable=False), sa.Column("customer_id", sa.UUID(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("subtotal", sa.Numeric(14,2), nullable=False), sa.Column("discount_amount", sa.Numeric(14,2), nullable=False), sa.Column("total", sa.Numeric(14,2), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("exchange_rate", sa.Numeric(10,4), nullable=False), sa.Column("exchange_rate_source", sa.String(50), nullable=True), sa.Column("exchange_rate_timestamp", sa.DateTime(timezone=True), nullable=True), sa.Column("valid_until", sa.Date(), nullable=False), sa.Column("notes", sa.Text(), nullable=True), sa.Column("converted_to_sale_id", sa.UUID(), nullable=True), sa.Column("sent_via_whatsapp", sa.Boolean(), nullable=False), sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_by", sa.UUID(), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("discount_amount >= 0", name=op.f("ck_quotes_discount_non_negative")), sa.CheckConstraint("subtotal >= 0", name=op.f("ck_quotes_subtotal_non_negative")), sa.CheckConstraint("total >= 0", name=op.f("ck_quotes_total_non_negative")), sa.ForeignKeyConstraint(["converted_to_sale_id"], ["sales.id"], name=op.f("fk_quotes_converted_to_sale_id_sales"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_quotes_created_by_users"), ondelete="SET NULL"), sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], name=op.f("fk_quotes_customer_id_customers"), ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id", name=op.f("pk_quotes")))
    op.create_index(op.f("ix_quotes_code"), "quotes", ["code"], unique=True)
    op.create_index(op.f("ix_quotes_created_by"), "quotes", ["created_by"], unique=False)
    op.create_index(op.f("ix_quotes_customer_id"), "quotes", ["customer_id"], unique=False)
    op.create_index(op.f("ix_quotes_status"), "quotes", ["status"], unique=False)
    op.create_index(op.f("ix_quotes_valid_until"), "quotes", ["valid_until"], unique=False)
    op.create_index("ix_quotes_status_created", "quotes", ["status", "created_at"], unique=False)
    op.create_table("quote_items", sa.Column("quote_id", sa.UUID(), nullable=False), sa.Column("product_id", sa.UUID(), nullable=False), sa.Column("quantity", sa.Numeric(14,3), nullable=False), sa.Column("unit_price", sa.Numeric(14,2), nullable=False), sa.Column("discount_amount", sa.Numeric(14,2), nullable=False), sa.Column("subtotal", sa.Numeric(14,2), nullable=False), sa.Column("notes", sa.Text(), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_quote_items_product_id_products"), ondelete="RESTRICT"), sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], name=op.f("fk_quote_items_quote_id_quotes"), ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_items")))
    op.create_index(op.f("ix_quote_items_product_id"), "quote_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_quote_items_quote_id"), "quote_items", ["quote_id"], unique=False)

    # --- whatsapp (#F06-07) ---
    op.create_table("whatsapp_templates", sa.Column("name", sa.String(100), nullable=False), sa.Column("event_type", sa.String(50), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("variables", pg.JSONB(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("id", name=op.f("pk_whatsapp_templates")), sa.UniqueConstraint("name", name=op.f("uq_whatsapp_templates_name")))
    op.create_index(op.f("ix_whatsapp_templates_event_type"), "whatsapp_templates", ["event_type"], unique=False)
    op.create_table("whatsapp_messages", sa.Column("recipient", sa.String(50), nullable=False), sa.Column("template_id", sa.UUID(), nullable=False), sa.Column("payload", pg.JSONB(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("idempotency_key", sa.String(200), nullable=False), sa.Column("provider_message_id", sa.String(120), nullable=True), sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True), sa.Column("error", sa.Text(), nullable=True), sa.Column("retry_count", sa.Integer(), nullable=False), sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["template_id"], ["whatsapp_templates.id"], name=op.f("fk_whatsapp_messages_template_id_whatsapp_templates"), ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id", name=op.f("pk_whatsapp_messages")), sa.UniqueConstraint("idempotency_key", name=op.f("uq_whatsapp_messages_idempotency_key")))
    op.create_index(op.f("ix_whatsapp_messages_idempotency_key"), "whatsapp_messages", ["idempotency_key"], unique=True)
    op.create_index(op.f("ix_whatsapp_messages_status"), "whatsapp_messages", ["status"], unique=False)
    op.create_index(op.f("ix_whatsapp_messages_template_id"), "whatsapp_messages", ["template_id"], unique=False)
    op.create_index("ix_whatsapp_messages_status_created", "whatsapp_messages", ["status", "created_at"], unique=False)
    op.create_table("whatsapp_delivery_logs", sa.Column("message_id", sa.UUID(), nullable=False), sa.Column("attempt_number", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("provider_response", pg.JSONB(), nullable=False), sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False), sa.Column("error", sa.Text(), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["message_id"], ["whatsapp_messages.id"], name=op.f("fk_whatsapp_delivery_logs_message_id_whatsapp_messages"), ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name=op.f("pk_whatsapp_delivery_logs")))
    op.create_index(op.f("ix_whatsapp_delivery_logs_message_id"), "whatsapp_delivery_logs", ["message_id"], unique=False)
    op.create_table("whatsapp_config", sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("provider", sa.String(30), nullable=False), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("id", name=op.f("pk_whatsapp_config")))

    # --- notifications (#F06-14) ---
    op.create_table("notifications", sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("type", sa.String(50), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("read", sa.Boolean(), nullable=False), sa.Column("priority", sa.String(10), nullable=False), sa.Column("related_type", sa.String(50), nullable=True), sa.Column("related_id", sa.UUID(), nullable=True), sa.Column("read_at", sa.DateTime(timezone=True), nullable=True), sa.Column("id", sa.UUID(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_notifications_user_id_users"), ondelete="CASCADE"), sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")))
    op.create_index(op.f("ix_notifications_read"), "notifications", ["read"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read"], unique=False)


def downgrade():
    op.drop_table("notifications")
    op.drop_table("whatsapp_config")
    op.drop_table("whatsapp_delivery_logs")
    op.drop_table("whatsapp_messages")
    op.drop_table("whatsapp_templates")
    op.drop_table("quote_items")
    op.drop_table("quotes")

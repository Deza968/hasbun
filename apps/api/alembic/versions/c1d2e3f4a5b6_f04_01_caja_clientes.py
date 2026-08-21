"""F04-01 - caja y clientes

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-08-21

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("first_name", sa.String(120), nullable=True),
        sa.Column("last_name", sa.String(120), nullable=True),
        sa.Column("razon_social", sa.String(255), nullable=True),
        sa.Column("dni", sa.String(8), nullable=True),
        sa.Column("ruc", sa.String(11), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("phone_whatsapp", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("credit_limit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("is_frequent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_customers_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("dni", name=op.f("uq_customers_dni")),
        sa.UniqueConstraint("ruc", name=op.f("uq_customers_ruc")),
    )

    op.create_table(
        "cash_registers",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("is_general", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_cash_registers_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_registers")),
    )
    op.create_index(op.f("ix_cash_registers_user_id"), "cash_registers", ["user_id"], unique=False)
    op.create_table(
        "cash_sessions",
        sa.Column("register_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("opening_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("expected_cash", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("counted_cash", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("difference", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_by", sa.UUID(), nullable=True),
        sa.Column("closed_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("difference = counted_cash - expected_cash", name=op.f("ck_cash_sessions_difference_check")),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"], name=op.f("fk_cash_sessions_closed_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opened_by"], ["users.id"], name=op.f("fk_cash_sessions_opened_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["register_id"], ["cash_registers.id"], name=op.f("fk_cash_sessions_register_id_cash_registers"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_cash_sessions_user_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_sessions")),
    )
    op.create_index(op.f("ix_cash_sessions_register_id"), "cash_sessions", ["register_id"], unique=False)
    op.create_index(op.f("ix_cash_sessions_status"), "cash_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_cash_sessions_user_id"), "cash_sessions", ["user_id"], unique=False)
    op.execute("CREATE UNIQUE INDEX ix_cash_sessions_user_open ON cash_sessions (user_id, status) WHERE status = 'OPEN'")

    op.create_table(
        "cash_movements",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("reference_type", sa.String(40), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("authorized_by", sa.UUID(), nullable=True),
        sa.Column("idempotency_key", sa.String(80), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount > 0", name=op.f("ck_cash_movements_amount_positive")),
        sa.ForeignKeyConstraint(["authorized_by"], ["users.id"], name=op.f("fk_cash_movements_authorized_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cash_movements_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["cash_sessions.id"], name=op.f("fk_cash_movements_session_id_cash_sessions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_movements")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_cash_movements_idempotency")),
    )
    op.create_index(op.f("ix_cash_movements_idempotency_key"), "cash_movements", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_cash_movements_session_id"), "cash_movements", ["session_id"], unique=False)
    op.create_index(op.f("ix_cash_movements_type"), "cash_movements", ["type"], unique=False)

    op.create_table(
        "cash_transfers",
        sa.Column("from_session_id", sa.UUID(), nullable=False),
        sa.Column("to_session_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("out_movement_id", sa.UUID(), nullable=True),
        sa.Column("in_movement_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cash_transfers_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_session_id"], ["cash_sessions.id"], name=op.f("fk_cash_transfers_from_session_id_cash_sessions"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["in_movement_id"], ["cash_movements.id"], name=op.f("fk_cash_transfers_in_movement_id_cash_movements"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["out_movement_id"], ["cash_movements.id"], name=op.f("fk_cash_transfers_out_movement_id_cash_movements"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_session_id"], ["cash_sessions.id"], name=op.f("fk_cash_transfers_to_session_id_cash_sessions"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_transfers")),
    )
    op.create_index(op.f("ix_cash_transfers_from_session_id"), "cash_transfers", ["from_session_id"], unique=False)
    op.create_index(op.f("ix_cash_transfers_to_session_id"), "cash_transfers", ["to_session_id"], unique=False)
    op.create_table(
        "cash_closure_requests",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("expected_cash", sa.Numeric(14, 2), nullable=False),
        sa.Column("counted_cash", sa.Numeric(14, 2), nullable=False),
        sa.Column("difference", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], name=op.f("fk_cash_closure_requests_requested_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], name=op.f("fk_cash_closure_requests_reviewed_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["cash_sessions.id"], name=op.f("fk_cash_closure_requests_session_id_cash_sessions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cash_closure_requests")),
    )
    op.create_index(op.f("ix_cash_closure_requests_session_id"), "cash_closure_requests", ["session_id"], unique=False)
    op.create_index(op.f("ix_cash_closure_requests_status"), "cash_closure_requests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cash_closure_requests_status"), table_name="cash_closure_requests")
    op.drop_index(op.f("ix_cash_closure_requests_session_id"), table_name="cash_closure_requests")
    op.drop_table("cash_closure_requests")
    op.drop_index(op.f("ix_cash_transfers_to_session_id"), table_name="cash_transfers")
    op.drop_index(op.f("ix_cash_transfers_from_session_id"), table_name="cash_transfers")
    op.drop_table("cash_transfers")
    op.drop_index(op.f("ix_cash_movements_type"), table_name="cash_movements")
    op.drop_index(op.f("ix_cash_movements_session_id"), table_name="cash_movements")
    op.drop_index(op.f("ix_cash_movements_idempotency_key"), table_name="cash_movements")
    op.drop_table("cash_movements")
    op.execute("DROP INDEX IF EXISTS ix_cash_sessions_user_open")
    op.drop_index(op.f("ix_cash_sessions_user_id"), table_name="cash_sessions")
    op.drop_index(op.f("ix_cash_sessions_status"), table_name="cash_sessions")
    op.drop_index(op.f("ix_cash_sessions_register_id"), table_name="cash_sessions")
    op.drop_table("cash_sessions")
    op.drop_index(op.f("ix_cash_registers_user_id"), table_name="cash_registers")
    op.drop_table("cash_registers")
    op.drop_table("customers")

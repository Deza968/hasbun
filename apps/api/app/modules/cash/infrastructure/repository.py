"""Repositorio de caja (#F04-02/03/04/05)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.cash.domain.models import (
    CashClosureRequest,
    CashMovement,
    CashRegister,
    CashSession,
    CashTransfer,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Registers
# ---------------------------------------------------------------------------


async def get_register(db: AsyncSession, register_id: uuid.UUID) -> CashRegister | None:
    return await db.get(CashRegister, register_id)


async def get_register_by_name(db: AsyncSession, name: str) -> CashRegister | None:
    result = await db.execute(select(CashRegister).where(CashRegister.name == name))
    return result.scalars().first()


async def list_registers(
    db: AsyncSession,
    *,
    active: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CashRegister], int]:
    query = select(CashRegister)
    count_query = select(func.count(CashRegister.id))
    if active is not None:
        query = query.where(CashRegister.active == active)
        count_query = count_query.where(CashRegister.active == active)
    total = (await db.execute(count_query)).scalar()
    query = query.order_by(CashRegister.created_at.desc()).offset((page - 1) * per_page)
    query = query.limit(per_page)
    items = (await db.execute(query)).scalars().all()
    return list(items), int(total or 0)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> CashSession | None:
    return await db.get(CashSession, session_id)


async def get_active_session(db: AsyncSession, user_id: uuid.UUID) -> CashSession | None:
    result = await db.execute(
        select(CashSession).where(CashSession.user_id == user_id, CashSession.status == "OPEN")
    )
    return result.scalars().first()


async def list_sessions(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    register_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CashSession], int]:
    query = select(CashSession)
    count_query = select(func.count(CashSession.id))
    if user_id is not None:
        query = query.where(CashSession.user_id == user_id)
        count_query = count_query.where(CashSession.user_id == user_id)
    if status is not None:
        query = query.where(CashSession.status == status)
        count_query = count_query.where(CashSession.status == status)
    if register_id is not None:
        query = query.where(CashSession.register_id == register_id)
        count_query = count_query.where(CashSession.register_id == register_id)
    total = (await db.execute(count_query)).scalar()
    query = query.order_by(CashSession.created_at.desc()).offset((page - 1) * per_page)
    query = query.limit(per_page)
    items = (await db.execute(query)).scalars().all()
    return list(items), int(total or 0)


async def get_balance(db: AsyncSession, session_id: uuid.UUID) -> Decimal:
    """Calcula balance: SUM IN - SUM OUT para una sesión."""
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (CashMovement.direction == "IN", CashMovement.amount),
                        else_=-CashMovement.amount,
                    )
                ),
                0,
            )
        ).where(CashMovement.session_id == session_id)
    )
    val = result.scalar()
    if val is None:
        return Decimal("0.00")
    # Asegurar Decimal con 2 decimales
    return Decimal(str(val)).quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Movements
# ---------------------------------------------------------------------------


async def get_movement_by_idempotency(
    db: AsyncSession, idempotency_key: str
) -> CashMovement | None:
    result = await db.execute(
        select(CashMovement).where(CashMovement.idempotency_key == idempotency_key)
    )
    return result.scalars().first()


async def get_movement(db: AsyncSession, movement_id: uuid.UUID) -> CashMovement | None:
    return await db.get(CashMovement, movement_id)


async def list_movements(
    db: AsyncSession,
    session_id: uuid.UUID,
    *,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[CashMovement], int]:
    query = select(CashMovement).where(CashMovement.session_id == session_id)
    count_query = select(func.count(CashMovement.id)).where(CashMovement.session_id == session_id)
    total = (await db.execute(count_query)).scalar()
    query = query.order_by(CashMovement.created_at.desc()).offset((page - 1) * per_page)
    query = query.limit(per_page)
    items = (await db.execute(query)).scalars().all()
    return list(items), int(total or 0)


# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------


async def get_transfer(db: AsyncSession, transfer_id: uuid.UUID) -> CashTransfer | None:
    return await db.get(CashTransfer, transfer_id)


# ---------------------------------------------------------------------------
# Closure requests
# ---------------------------------------------------------------------------


async def get_closure_request(
    db: AsyncSession, request_id: uuid.UUID
) -> CashClosureRequest | None:
    return await db.get(CashClosureRequest, request_id)


async def get_pending_closure_for_session(
    db: AsyncSession, session_id: uuid.UUID
) -> CashClosureRequest | None:
    result = await db.execute(
        select(CashClosureRequest).where(
            CashClosureRequest.session_id == session_id,
            CashClosureRequest.status == "PENDING",
        )
    )
    return result.scalars().first()


async def list_closure_requests(
    db: AsyncSession,
    *,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CashClosureRequest], int]:
    query = select(CashClosureRequest)
    count_query = select(func.count(CashClosureRequest.id))
    if status is not None:
        query = query.where(CashClosureRequest.status == status)
        count_query = count_query.where(CashClosureRequest.status == status)
    total = (await db.execute(count_query)).scalar()
    query = (
        query.order_by(CashClosureRequest.requested_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = (await db.execute(query)).scalars().all()
    return list(items), int(total or 0)

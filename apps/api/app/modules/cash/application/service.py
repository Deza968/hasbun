"""Servicio de caja (#F04-02/03/04/05)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from app.modules.audit.application.service import log
from app.modules.cash.domain.models import (
    CashClosureRequest,
    CashMovement,
    CashSession,
    CashTransfer,
)
from app.modules.cash.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def get_session_balance(db: AsyncSession, session_id: uuid.UUID) -> Decimal:
    return await repository.get_balance(db, session_id)


async def get_active_session(db: AsyncSession, user_id: uuid.UUID) -> CashSession | None:
    return await repository.get_active_session(db, user_id)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


async def create_register(
    db: AsyncSession, *, name: str, user_id: uuid.UUID | None, is_general: bool, created_by: User
):
    from app.modules.cash.domain.models import CashRegister

    register = CashRegister(name=name, user_id=user_id, is_general=is_general, active=True)
    db.add(register)
    await db.commit()
    await db.refresh(register)
    await log(
        action="CREATE_CASH_REGISTER",
        module="cash",
        user_id=created_by.id,
        entity_type="CashRegister",
        entity_id=register.id,
        new_values={"name": register.name},
    )
    return register


# ---------------------------------------------------------------------------
# Open session
# ---------------------------------------------------------------------------


async def open_session(
    db: AsyncSession, *, register_id: uuid.UUID, opening_amount: Decimal, user: User
) -> CashSession:
    # Verificar registro existe
    register = await repository.get_register(db, register_id)
    if register is None:
        raise NotFoundError("Caja no encontrada")
    if not register.active:
        raise ValidationError("La caja está inactiva")

    # Verificar solo 1 OPEN por user (partial unique index)
    existing = await repository.get_active_session(db, user.id)
    if existing is not None:
        raise ConflictError("Ya tienes una sesión de caja abierta")

    now = datetime.now(UTC)
    session = CashSession(
        register_id=register_id,
        user_id=user.id,
        status="OPEN",
        opening_amount=opening_amount.quantize(Decimal("0.01")),
        expected_cash=Decimal("0.00"),
        counted_cash=Decimal("0.00"),
        difference=Decimal("0.00"),
        opened_at=now,
        opened_by=user.id,
    )
    db.add(session)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        # partial unique index violation
        raise ConflictError("Ya tienes una sesión de caja abierta") from exc

    # Movimiento de apertura si opening_amount > 0 ; siempre crear si >0
    if opening_amount > 0:
        movement = CashMovement(
            session_id=session.id,
            type="OPENING",
            amount=opening_amount.quantize(Decimal("0.01")),
            direction="IN",
            reason="Apertura de caja",
            created_by=user.id,
        )
        db.add(movement)
        await db.flush()
    else:
        # Aun con 0, creamos movimiento OPENING de 0? No, constraint amount>0, entonces skip
        pass

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("Ya tienes una sesión de caja abierta") from exc

    await db.refresh(session)
    await log(
        action="OPEN_CASH_SESSION",
        module="cash",
        user_id=user.id,
        entity_type="CashSession",
        entity_id=session.id,
        new_values={"register_id": str(register_id), "opening_amount": str(opening_amount)},
    )
    return session


# ---------------------------------------------------------------------------
# Movements
# ---------------------------------------------------------------------------


async def add_movement(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    type: str,  # noqa: A002
    amount: Decimal,
    direction: str,
    reference_type: str | None = None,
    reference_id: uuid.UUID | None = None,
    reason: str | None = None,
    authorized_by: uuid.UUID | None = None,
    idempotency_key: str | None = None,
    created_by: User | uuid.UUID | None = None,
) -> CashMovement:
    if amount <= 0:
        raise ValidationError("El monto debe ser mayor que 0")

    # Idempotencia
    if idempotency_key:
        existing = await repository.get_movement_by_idempotency(db, idempotency_key)
        if existing is not None:
            return existing

    session = await repository.get_session(db, session_id)
    if session is None:
        raise NotFoundError("Sesión de caja no encontrada")
    if session.status != "OPEN":
        raise BusinessRuleError("La sesión no está abierta")

    creator_id: uuid.UUID | None = None
    if isinstance(created_by, User):
        creator_id = created_by.id
    elif isinstance(created_by, uuid.UUID):
        creator_id = created_by

    movement = CashMovement(
        session_id=session_id,
        type=type,
        amount=amount.quantize(Decimal("0.01")),
        direction=direction,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
        authorized_by=authorized_by,
        idempotency_key=idempotency_key,
        created_by=creator_id,
    )
    db.add(movement)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # idempotency duplicate
        if idempotency_key:
            existing = await repository.get_movement_by_idempotency(db, idempotency_key)
            if existing is not None:
                return existing
        raise ConflictError("Movimiento duplicado (idempotency_key)") from exc
    await db.refresh(movement)

    # Audit si es manual
    if type in ("OTHER_INCOME", "EXPENSE", "OPENING", "TRANSFER_IN", "TRANSFER_OUT"):
        await log(
            action="CASH_MOVEMENT",
            module="cash",
            user_id=creator_id,
            entity_type="CashMovement",
            entity_id=movement.id,
            new_values={"type": type, "amount": str(amount), "session_id": str(session_id)},
        )
    return movement


async def add_income(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    amount: Decimal,
    reason: str,
    user: User,
    idempotency_key: str | None = None,
) -> CashMovement:
    if not reason or not reason.strip():
        raise ValidationError("El motivo es obligatorio")
    return await add_movement(
        db,
        session_id=session_id,
        type="OTHER_INCOME",
        amount=amount,
        direction="IN",
        reason=reason.strip(),
        authorized_by=user.id,
        idempotency_key=idempotency_key,
        created_by=user,
    )


async def add_expense(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    amount: Decimal,
    reason: str,
    user: User,
    idempotency_key: str | None = None,
) -> CashMovement:
    if not reason or not reason.strip():
        raise ValidationError("El motivo es obligatorio")
    # Verificar saldo suficiente? Egreso no debe dejar balance negativo? Opcional pero útil
    balance = await repository.get_balance(db, session_id)
    if balance < amount:
        raise BusinessRuleError(f"Saldo insuficiente: disponible {balance}, requerido {amount}")
    return await add_movement(
        db,
        session_id=session_id,
        type="EXPENSE",
        amount=amount,
        direction="OUT",
        reason=reason.strip(),
        authorized_by=user.id,
        idempotency_key=idempotency_key,
        created_by=user,
    )


# ---------------------------------------------------------------------------
# Close session
# ---------------------------------------------------------------------------


async def request_close_session(
    db: AsyncSession, *, session_id: uuid.UUID, counted_cash: Decimal, user: User
) -> tuple[CashSession, CashClosureRequest | None]:
    session = await repository.get_session(db, session_id)
    if session is None:
        raise NotFoundError("Sesión no encontrada")
    if session.status != "OPEN":
        raise BusinessRuleError("La sesión no está abierta")
    # Router valida permiso; aquí no bloqueamos por dueño,
    # cualquier usuario con permiso caja.cerrar puede cerrar su sesión.

    expected = await repository.get_balance(db, session_id)
    counted = counted_cash.quantize(Decimal("0.01"))
    diff = (counted - expected).quantize(Decimal("0.01"))

    session.expected_cash = expected
    session.counted_cash = counted
    session.difference = diff

    if diff == Decimal("0.00"):
        session.status = "CLOSED"
        session.closed_at = datetime.now(UTC)
        session.closed_by = user.id
        await db.commit()
        await db.refresh(session)
        await log(
            action="CLOSE_CASH_SESSION",
            module="cash",
            user_id=user.id,
            entity_type="CashSession",
            entity_id=session.id,
            new_values={
                "expected": str(expected),
                "counted": str(counted),
                "difference": str(diff),
            },
        )
        return session, None
    # Diferencia !=0 -> PENDING_CLOSURE
    session.status = "PENDING_CLOSURE"
    # closed_at aún no, se cierra al aprobar
    closure = CashClosureRequest(
        session_id=session.id,
        expected_cash=expected,
        counted_cash=counted,
        difference=diff,
        status="PENDING",
        requested_by=user.id,
        requested_at=datetime.now(UTC),
    )
    db.add(closure)
    await db.commit()
    await db.refresh(session)
    await db.refresh(closure)
    await log(
        action="REQUEST_CASH_CLOSURE",
        module="cash",
        user_id=user.id,
        entity_type="CashClosureRequest",
        entity_id=closure.id,
        new_values={
            "expected": str(expected),
            "counted": str(counted),
            "difference": str(diff),
        },
    )
    return session, closure


async def approve_closure(
    db: AsyncSession, *, request_id: uuid.UUID, reason: str | None, approved_by: User
) -> tuple[CashSession, CashClosureRequest]:
    closure = await repository.get_closure_request(db, request_id)
    if closure is None:
        raise NotFoundError("Solicitud de cierre no encontrada")
    if closure.status != "PENDING":
        raise BusinessRuleError("La solicitud ya fue procesada")
    session = await repository.get_session(db, closure.session_id)
    if session is None:
        raise NotFoundError("Sesión no encontrada")
    if session.status != "PENDING_CLOSURE":
        raise BusinessRuleError("La sesión no está pendiente de cierre")

    closure.status = "APPROVED"
    closure.reviewed_by = approved_by.id
    closure.reviewed_at = datetime.now(UTC)
    closure.review_reason = reason

    session.status = "CLOSED"
    session.closed_at = datetime.now(UTC)
    session.closed_by = approved_by.id

    await db.commit()
    await db.refresh(session)
    await db.refresh(closure)
    await log(
        action="APPROVE_CASH_CLOSURE",
        module="cash",
        user_id=approved_by.id,
        entity_type="CashClosureRequest",
        entity_id=closure.id,
        new_values={"difference": str(closure.difference), "reason": reason},
    )
    return session, closure


async def reject_closure(
    db: AsyncSession, *, request_id: uuid.UUID, reason: str | None, rejected_by: User
) -> tuple[CashSession, CashClosureRequest]:
    closure = await repository.get_closure_request(db, request_id)
    if closure is None:
        raise NotFoundError("Solicitud de cierre no encontrada")
    if closure.status != "PENDING":
        raise BusinessRuleError("La solicitud ya fue procesada")
    session = await repository.get_session(db, closure.session_id)
    if session is None:
        raise NotFoundError("Sesión no encontrada")
    if session.status != "PENDING_CLOSURE":
        raise BusinessRuleError("La sesión no está pendiente de cierre")

    closure.status = "REJECTED"
    closure.reviewed_by = rejected_by.id
    closure.reviewed_at = datetime.now(UTC)
    closure.review_reason = reason

    session.status = "OPEN"
    # reset expected/counted/difference ? Mantener pero resetear para permitir nuevo cierre.
    # Según spec, vuelve a OPEN; mantenemos valores pero no afecta balance.
    # Opcional reset a 0? Dejamos como está para auditoría, pero diferencia permanece.
    await db.commit()
    await db.refresh(session)
    await db.refresh(closure)
    await log(
        action="REJECT_CASH_CLOSURE",
        module="cash",
        user_id=rejected_by.id,
        entity_type="CashClosureRequest",
        entity_id=closure.id,
        new_values={"reason": reason},
    )
    return session, closure


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


async def transfer_between_sessions(
    db: AsyncSession,
    *,
    from_session_id: uuid.UUID,
    to_session_id: uuid.UUID,
    amount: Decimal,
    reason: str | None,
    user: User,
) -> CashTransfer:
    if from_session_id == to_session_id:
        raise ValidationError("No se puede transferir a la misma sesión")
    if amount <= 0:
        raise ValidationError("El monto debe ser mayor que 0")

    from_session = await repository.get_session(db, from_session_id)
    to_session = await repository.get_session(db, to_session_id)
    if from_session is None or to_session is None:
        raise NotFoundError("Sesión no encontrada")
    if from_session.status != "OPEN" or to_session.status != "OPEN":
        raise BusinessRuleError("Ambas sesiones deben estar abiertas")

    balance = await repository.get_balance(db, from_session_id)
    if balance < amount:
        raise BusinessRuleError(
            f"Saldo insuficiente en origen: disponible {balance}, requerido {amount}"
        )

    # Transacción atómica
    try:
        # AsyncSession ya tiene transaction; usamos flush + commit atómico
        out_mov = CashMovement(
            session_id=from_session_id,
            type="TRANSFER_OUT",
            amount=amount.quantize(Decimal("0.01")),
            direction="OUT",
            reason=reason,
            created_by=user.id,
        )
        db.add(out_mov)
        await db.flush()

        in_mov = CashMovement(
            session_id=to_session_id,
            type="TRANSFER_IN",
            amount=amount.quantize(Decimal("0.01")),
            direction="IN",
            reason=reason,
            created_by=user.id,
        )
        db.add(in_mov)
        await db.flush()

        transfer = CashTransfer(
            from_session_id=from_session_id,
            to_session_id=to_session_id,
            amount=amount.quantize(Decimal("0.01")),
            reason=reason,
            out_movement_id=out_mov.id,
            in_movement_id=in_mov.id,
            created_by=user.id,
        )
        db.add(transfer)
        await db.flush()
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(transfer)
    await log(
        action="TRANSFER_CASH",
        module="cash",
        user_id=user.id,
        entity_type="CashTransfer",
        entity_id=transfer.id,
        new_values={
            "from": str(from_session_id),
            "to": str(to_session_id),
            "amount": str(amount),
        },
    )
    return transfer

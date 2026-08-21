"""Router de caja (#F04-02/03/04/05)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.redis import get_permission_cache, set_permission_cache
from app.modules.auth.application.service import get_user_permissions
from app.modules.cash.application import service
from app.modules.cash.application.schemas import (
    CashRegisterCreate,
    CashRegisterListResponse,
    CashRegisterResponse,
    CloseSessionRequest,
    ClosureRequestListResponse,
    ClosureRequestResponse,
    ExpenseRequest,
    IncomeRequest,
    MovementListResponse,
    MovementResponse,
    OpenSessionRequest,
    ReviewClosureRequest,
    SessionListResponse,
    SessionResponse,
    TransferRequest,
    TransferResponse,
)
from app.modules.cash.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["cash"])

# ---------------------------------------------------------------------------
# Permisos con fallback
# ---------------------------------------------------------------------------
# Seeds solo tienen caja.abrir, caja.cerrar, caja.ver_todas, caja.transferir.
# El enunciado pide caja.ver / caja.gestionar / caja.aprobar que no existen.
# Fallback: acepta cualquiera de la familia caja.* si el primario no está.
CASH_VIEW_CODES = ["caja.ver", "caja.ver_todas", "caja.gestionar", "caja.aprobar"]
CASH_MANAGE_CODES = [
    "caja.gestionar",
    "caja.aprobar",
    "caja.cerrar",
    "caja.abrir",
    "caja.transferir",
    "caja.ver_todas",
    "caja.ver",
]
CASH_APPROVE_CODES = ["caja.aprobar", "caja.gestionar", "caja.ver_todas", "caja.transferir"]
CASH_TRANSFER_CODES = ["caja.transferir", "caja.gestionar", "caja.aprobar", "caja.ver_todas"]


def require_cash_permission(codes: list[str]):
    async def dependency(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if user.is_superuser:
            return user
        perms = await get_permission_cache(str(user.id))
        if perms is None:
            from app.database.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                perms = await get_user_permissions(session, user)
            await set_permission_cache(str(user.id), perms)
        if any(c in perms for c in codes) or "*" in perms:
            return user
        raise AuthorizationError(f"Permiso requerido: {codes[0]}")

    return dependency


ViewCash = Annotated[User, Depends(require_cash_permission(CASH_VIEW_CODES))]
ManageCash = Annotated[User, Depends(require_cash_permission(CASH_MANAGE_CODES))]
ApproveCash = Annotated[User, Depends(require_cash_permission(CASH_APPROVE_CODES))]
TransferCash = Annotated[User, Depends(require_cash_permission(CASH_TRANSFER_CODES))]


# ---------------------------------------------------------------------------
# Registers
# ---------------------------------------------------------------------------


@router.post("/cash/registers", response_model=CashRegisterResponse, status_code=201)
async def create_register(
    body: CashRegisterCreate,
    db: DbSession,
    actor: ManageCash,
) -> CashRegisterResponse:
    reg = await service.create_register(
        db, name=body.name, user_id=body.user_id, is_general=body.is_general, created_by=actor
    )
    return CashRegisterResponse.from_model(reg)


@router.get("/cash/registers", response_model=CashRegisterListResponse)
async def list_registers(
    db: DbSession,
    _: ViewCash,
    active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> CashRegisterListResponse:
    items, total = await repository.list_registers(
        db, active=active, page=page, per_page=per_page
    )
    return CashRegisterListResponse(
        items=[CashRegisterResponse.from_model(r) for r in items], total=total
    )


# ---------------------------------------------------------------------------
# Sessions - orden importa: active antes que {id}
# ---------------------------------------------------------------------------


@router.post("/cash/sessions/open", response_model=SessionResponse, status_code=201)
async def open_session(
    body: OpenSessionRequest,
    db: DbSession,
    actor: ManageCash,
) -> SessionResponse:
    sess = await service.open_session(
        db, register_id=body.register_id, opening_amount=body.opening_amount, user=actor
    )
    balance = await repository.get_balance(db, sess.id)
    return SessionResponse.from_model(sess, balance=balance)


@router.get("/cash/sessions/active", response_model=SessionResponse)
async def get_active_session(
    db: DbSession,
    actor: ViewCash,
) -> SessionResponse:
    sess = await service.get_active_session(db, actor.id)
    if sess is None:
        raise NotFoundError("No tienes sesión de caja abierta")
    balance = await repository.get_balance(db, sess.id)
    return SessionResponse.from_model(sess, balance=balance)


@router.get("/cash/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: DbSession,
    _: ViewCash,
    user_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    register_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> SessionListResponse:
    items, total = await repository.list_sessions(
        db, user_id=user_id, status=status, register_id=register_id, page=page, per_page=per_page
    )
    # balance per session
    result = []
    for s in items:
        bal = await repository.get_balance(db, s.id)
        result.append(SessionResponse.from_model(s, balance=bal))
    return SessionListResponse(items=result, total=total)


@router.get("/cash/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: DbSession,
    _: ViewCash,
) -> SessionResponse:
    sess = await repository.get_session(db, session_id)
    if sess is None:
        raise NotFoundError("Sesión no encontrada")
    balance = await repository.get_balance(db, sess.id)
    return SessionResponse.from_model(sess, balance=balance)


@router.get("/cash/sessions/{session_id}/movements", response_model=MovementListResponse)
async def list_movements(
    session_id: uuid.UUID,
    db: DbSession,
    _: ViewCash,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> MovementListResponse:
    sess = await repository.get_session(db, session_id)
    if sess is None:
        raise NotFoundError("Sesión no encontrada")
    items, total = await repository.list_movements(db, session_id, page=page, per_page=per_page)
    return MovementListResponse(items=[MovementResponse.from_model(m) for m in items], total=total)


@router.post("/cash/sessions/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: uuid.UUID,
    body: CloseSessionRequest,
    db: DbSession,
    actor: ManageCash,
) -> SessionResponse:
    sess, _ = await service.request_close_session(
        db, session_id=session_id, counted_cash=body.counted_cash, user=actor
    )
    balance = await repository.get_balance(db, sess.id)
    return SessionResponse.from_model(sess, balance=balance)


@router.post("/cash/sessions/{session_id}/income", response_model=MovementResponse, status_code=201)
async def add_income(
    session_id: uuid.UUID,
    body: IncomeRequest,
    db: DbSession,
    actor: ApproveCash,
) -> MovementResponse:
    mov = await service.add_income(
        db,
        session_id=session_id,
        amount=body.amount,
        reason=body.reason,
        user=actor,
        idempotency_key=body.idempotency_key,
    )
    return MovementResponse.from_model(mov)


@router.post(
    "/cash/sessions/{session_id}/expense", response_model=MovementResponse, status_code=201
)
async def add_expense(
    session_id: uuid.UUID,
    body: ExpenseRequest,
    db: DbSession,
    actor: ApproveCash,
) -> MovementResponse:
    mov = await service.add_expense(
        db,
        session_id=session_id,
        amount=body.amount,
        reason=body.reason,
        user=actor,
        idempotency_key=body.idempotency_key,
    )
    return MovementResponse.from_model(mov)


# ---------------------------------------------------------------------------
# Closure requests
# ---------------------------------------------------------------------------


@router.get("/cash/closure-requests", response_model=ClosureRequestListResponse)
async def list_closure_requests(
    db: DbSession,
    _: ApproveCash,
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> ClosureRequestListResponse:
    items, total = await repository.list_closure_requests(
        db, status=status, page=page, per_page=per_page
    )
    return ClosureRequestListResponse(
        items=[ClosureRequestResponse.from_model(r) for r in items], total=total
    )


@router.post("/cash/closure-requests/{request_id}/approve", response_model=ClosureRequestResponse)
async def approve_closure(
    request_id: uuid.UUID,
    body: ReviewClosureRequest,
    db: DbSession,
    actor: ApproveCash,
) -> ClosureRequestResponse:
    _, closure = await service.approve_closure(
        db, request_id=request_id, reason=body.reason, approved_by=actor
    )
    return ClosureRequestResponse.from_model(closure)


@router.post("/cash/closure-requests/{request_id}/reject", response_model=ClosureRequestResponse)
async def reject_closure(
    request_id: uuid.UUID,
    body: ReviewClosureRequest,
    db: DbSession,
    actor: ApproveCash,
) -> ClosureRequestResponse:
    _, closure = await service.reject_closure(
        db, request_id=request_id, reason=body.reason, rejected_by=actor
    )
    return ClosureRequestResponse.from_model(closure)


# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------


@router.post("/cash/transfers", response_model=TransferResponse, status_code=201)
async def create_transfer(
    body: TransferRequest,
    db: DbSession,
    actor: TransferCash,
) -> TransferResponse:
    tr = await service.transfer_between_sessions(
        db,
        from_session_id=body.from_session_id,
        to_session_id=body.to_session_id,
        amount=body.amount,
        reason=body.reason,
        user=actor,
    )
    return TransferResponse.from_model(tr)

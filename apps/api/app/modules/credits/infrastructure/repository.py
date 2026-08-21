"""Repositorio de créditos: solo consultas (#F05)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from app.modules.credits.domain.models import (
    AgreementStatus,
    CreditAgreement,
    CreditInstallment,
    InstallmentStatus,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_agreement(db: AsyncSession, agreement_id: uuid.UUID) -> CreditAgreement | None:
    return (
        await db.execute(
            select(CreditAgreement)
            .where(CreditAgreement.id == agreement_id)
            .options(selectinload(CreditAgreement.installments))
        )
    ).scalar_one_or_none()


async def get_installment(db: AsyncSession, installment_id: uuid.UUID) -> CreditInstallment | None:
    return (
        await db.execute(
            select(CreditInstallment)
            .where(CreditInstallment.id == installment_id)
            .options(selectinload(CreditInstallment.agreement))
        )
    ).scalar_one_or_none()


async def list_agreements(
    db: AsyncSession,
    *,
    status: str | None = None,
    customer_id: uuid.UUID | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[CreditAgreement], int]:
    q = select(CreditAgreement).options(selectinload(CreditAgreement.installments), selectinload(CreditAgreement.customer))
    count_q = select(func.count(CreditAgreement.id))
    if status:
        q = q.where(CreditAgreement.status == status)
        count_q = count_q.where(CreditAgreement.status == status)
    if customer_id:
        q = q.where(CreditAgreement.customer_id == customer_id)
        count_q = count_q.where(CreditAgreement.customer_id == customer_id)
    if search:
        like = f"%{search}%"
        cond = CreditAgreement.code.ilike(like)
        q = q.where(cond)
        count_q = count_q.where(cond)
    q = q.order_by(CreditAgreement.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    items = (await db.execute(q)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(items), int(total)


async def list_installments(
    db: AsyncSession,
    *,
    status: str | None = None,
    customer_id: uuid.UUID | None = None,
    due_before: date | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[CreditInstallment], int]:
    q = select(CreditInstallment).join(CreditAgreement).options(selectinload(CreditInstallment.agreement))
    count_q = select(func.count(CreditInstallment.id)).join(CreditAgreement)
    if status:
        q = q.where(CreditInstallment.status == status)
        count_q = count_q.where(CreditInstallment.status == status)
    if customer_id:
        q = q.where(CreditAgreement.customer_id == customer_id)
        count_q = count_q.where(CreditAgreement.customer_id == customer_id)
    if due_before:
        q = q.where(CreditInstallment.due_date <= due_before)
        count_q = count_q.where(CreditInstallment.due_date <= due_before)
    q = q.order_by(CreditInstallment.due_date.asc(), CreditInstallment.number.asc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    items = (await db.execute(q)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(items), int(total)


async def active_pending_total(db: AsyncSession, customer_id: uuid.UUID) -> Decimal:
    """SUM(remaining_amount) de cuotas PENDING/PARTIALLY_PAID de acuerdos vigentes (#F05-04)."""
    row = (
        await db.execute(
            select(func.coalesce(func.sum(CreditInstallment.remaining_amount), 0)).join(
                CreditAgreement, CreditInstallment.agreement_id == CreditAgreement.id
            ).where(
                CreditAgreement.customer_id == customer_id,
                CreditAgreement.status.in_(AgreementStatus.ALL - {AgreementStatus.PAID, AgreementStatus.CANCELLED}),
                CreditInstallment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.PARTIALLY_PAID]),
            )
        )
    ).scalar()
    return Decimal(row or 0)


async def has_overdue_for_customer(db: AsyncSession, customer_id: uuid.UUID) -> bool:
    """Morosidad por FECHA (#F05-04): cuota impaga con vencimiento pasado.

    No depende de que la tarea de mora haya marcado OVERDUE: una cuota
    PENDING/PARTIALLY_PAID con `due_date < hoy` ya es mora.
    """
    row = (
        await db.execute(
            select(CreditInstallment.id).join(
                CreditAgreement, CreditInstallment.agreement_id == CreditAgreement.id
            ).where(
                CreditAgreement.customer_id == customer_id,
                CreditInstallment.due_date < date.today(),
                CreditInstallment.status.in_([
                    InstallmentStatus.PENDING,
                    InstallmentStatus.PARTIALLY_PAID,
                    InstallmentStatus.OVERDUE,
                ]),
            ).limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def has_active_agreements(db: AsyncSession, customer_id: uuid.UUID) -> bool:
    row = (
        await db.execute(
            select(CreditAgreement.id).where(
                CreditAgreement.customer_id == customer_id,
                CreditAgreement.status.in_([AgreementStatus.ACTIVE, AgreementStatus.OVERDUE]),
            ).limit(1)
        )
    ).scalar_one_or_none()
    return row is not None


async def delinquency_summary(db: AsyncSession) -> dict[str, Any]:
    """Clientes con cuotas vencidas para la vista Morosidad (#F05-14).

    `oldest_due` = fecha de vencimiento más antigua por cliente → días de
    atraso se calculan en el router como hoy − oldest_due.
    """
    rows = (
        await db.execute(
            select(
                CreditAgreement.customer_id,
                func.count(func.distinct(CreditAgreement.id)).label("active_credits"),
                func.count(CreditInstallment.id).label("overdue_count"),
                func.coalesce(func.sum(CreditInstallment.remaining_amount), 0).label("overdue_capital"),
                func.coalesce(func.sum(CreditInstallment.mora_amount), 0).label("mora_total"),
                func.min(CreditInstallment.due_date).label("oldest_due"),
            ).join(CreditAgreement, CreditInstallment.agreement_id == CreditAgreement.id).where(
                CreditInstallment.status == InstallmentStatus.OVERDUE
            ).group_by(CreditAgreement.customer_id)
        )
    ).all()

    mora_total = (
        await db.execute(select(func.coalesce(func.sum(CreditInstallment.mora_amount), 0)))
    ).scalar() or Decimal("0")

    return {"rows": rows, "mora_system_total": Decimal(mora_total)}

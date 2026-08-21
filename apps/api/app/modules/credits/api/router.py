"""Router de créditos y cuotas (#F05)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user, require_permission
from app.core.exceptions import NotFoundError
from app.modules.credits.application import service
from app.modules.credits.application.schemas import (
    CreditListResponse,
    CreditResponse,
    CreditSaleCreate,
    CreditSummaryResponse,
    CreditValidateIn,
    DelinquencyResponse,
    DelinquencyRow,
    InstallmentListResponse,
    InstallmentOut,
    PayMultipleRequest,
    PayRequest,
    RestructureRequest,
    ValidationResponse,
)
from app.modules.credits.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["credits"])

ViewCredits = Annotated[User, Depends(require_permission("creditos.ver"))]
CreateCredits = Annotated[User, Depends(require_permission("ventas.crear"))]
ApproveCredits = Annotated[User, Depends(require_permission("creditos.aprobar"))]
ManageInstallments = Annotated[User, Depends(require_permission("cuotas.gestionar"))]
AnyUser = Annotated[User, Depends(get_current_active_user)]


@router.post("/credits/validate", response_model=ValidationResponse)
async def validate_credit(body: CreditValidateIn, db: DbSession, _: CreateCredits):
    """Verificación pre-crédito en tiempo real (#F05-04/#F05-12)."""
    return await service.validate_customer_for_credit(
        db,
        customer_id=body.customer_id,
        total_amount=body.total_amount,
        initial_payment=body.initial_payment,
        number_of_installments=body.number_of_installments,
        authorization_ids=body.authorization_ids,
    )


@router.post("/credits", response_model=CreditResponse, status_code=201)
async def create_credit(body: CreditSaleCreate, db: DbSession, actor: CreateCredits):
    agreement = await service.create_credit_sale(db, data=body, user=actor)
    return CreditResponse.from_model(agreement)


@router.get("/credits/my", response_model=list[CreditResponse])
async def my_credits(db: DbSession, actor: AnyUser):
    """Portal del cliente: créditos vinculados a su usuario (#F05-15)."""
    from app.modules.customers.domain.models import Customer
    from sqlalchemy import select

    customer_id = actor.id
    row = (await db.execute(select(Customer).where(Customer.user_id == actor.id))).scalars().first()
    if row is not None:
        customer_id = row.id
    else:
        return []
    agreements = await service.customer_credits(db, customer_id)
    return [CreditResponse.from_model(a) for a in agreements]


@router.get("/credits/delinquency", response_model=DelinquencyResponse)
async def delinquency(db: DbSession, _: ApproveCredits):
    """Resumen de morosidad — solo OWNER (#F05-14)."""
    from app.modules.customers.domain.models import Customer

    data = await repository.delinquency_summary(db)
    rows = []
    today = date.today()
    for r in data["rows"]:
        customer = await db.get(Customer, r.customer_id)
        name = None
        if customer is not None:
            name = customer.razon_social or " ".join(filter(None, [customer.first_name, customer.last_name])) or None
        days_late = max(0, (today - r.oldest_due).days) if r.oldest_due else 0
        rows.append(
            DelinquencyRow(
                customer_id=r.customer_id,
                customer_name=name,
                active_credits=int(r.active_credits),
                overdue_installments=int(r.overdue_count),
                overdue_capital=r.overdue_capital,
                mora_total=r.mora_total,
                days_late_max=days_late,
            )
        )
    return DelinquencyResponse(
        rows=rows,
        mora_system_total=data["mora_system_total"],
        affected_customers=len(rows),
    )


@router.get("/credits", response_model=CreditListResponse)
async def list_credits(
    db: DbSession,
    _: ViewCredits,
    status: str | None = Query(None),
    customer_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    items, total = await repository.list_agreements(
        db, status=status, customer_id=customer_id, search=search, page=page, per_page=per_page
    )
    out = []
    for a in items:
        paid_count = sum(1 for i in a.installments if i.status == "PAID")
        overdue_count = sum(1 for i in a.installments if i.status == "OVERDUE")
        pending_total = sum((i.remaining_amount + i.mora_amount) for i in a.installments if i.status != "PAID")
        c = a.customer
        out.append(
            CreditSummaryResponse(
                id=a.id,
                code=a.code,
                customer_id=a.customer_id,
                customer_name=(c.razon_social if c and c.razon_social else f"{c.first_name} {c.last_name}" if c else None),
                status=a.status,
                total_amount=a.total_amount,
                financed_amount=a.financed_amount,
                number_of_installments=a.number_of_installments,
                paid_installments=paid_count,
                overdue_installments=overdue_count,
                pending_total=pending_total,
                created_at=a.created_at,
            )
        )
    return CreditListResponse(items=out, total=total)


@router.get("/credits/customer/{customer_id}", response_model=CreditListResponse)
async def customer_credits(customer_id: uuid.UUID, db: DbSession, _: ViewCredits):
    items, total = await repository.list_agreements(db, customer_id=customer_id, per_page=100)
    out = [
        CreditSummaryResponse(
            id=a.id,
            code=a.code,
            customer_id=a.customer_id,
            status=a.status,
            total_amount=a.total_amount,
            financed_amount=a.financed_amount,
            number_of_installments=a.number_of_installments,
            paid_installments=sum(1 for i in a.installments if i.status == "PAID"),
            overdue_installments=sum(1 for i in a.installments if i.status == "OVERDUE"),
            pending_total=sum((i.remaining_amount + i.mora_amount) for i in a.installments if i.status != "PAID"),
            created_at=a.created_at,
        )
        for a in items
    ]
    return CreditListResponse(items=out, total=total)


@router.get("/installments", response_model=InstallmentListResponse)
async def list_installments(
    db: DbSession,
    _: ViewCredits,
    status: str | None = Query(None),
    customer_id: uuid.UUID | None = Query(None),
    due_before: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    items, total = await repository.list_installments(
        db, status=status, customer_id=customer_id, due_before=due_before, page=page, per_page=per_page
    )
    return InstallmentListResponse(items=[InstallmentOut.from_model(i) for i in items], total=total)


@router.get("/installments/{installment_id}", response_model=InstallmentOut)
async def get_installment(installment_id: uuid.UUID, db: DbSession, _: ViewCredits):
    inst = await repository.get_installment(db, installment_id)
    if inst is None:
        raise NotFoundError("Cuota no encontrada")
    return InstallmentOut.from_model(inst)


@router.post("/installments/{installment_id}/pay", response_model=dict)
async def pay_installment(installment_id: uuid.UUID, body: PayRequest, db: DbSession, actor: ManageInstallments):
    payment = await service.pay_installment(db, installment_id=installment_id, data=body, user=actor)
    return {
        "id": str(payment.id),
        "installment_id": str(payment.installment_id),
        "amount": str(payment.amount),
        "method": payment.method,
    }


@router.put("/installments/{installment_id}/restructure", response_model=InstallmentOut)
async def restructure_installment(
    installment_id: uuid.UUID, body: RestructureRequest, db: DbSession, actor: ManageInstallments
):
    """Reprogramación de cuota — solo OWNER (#F05-10)."""
    inst = await service.restructure_installment(
        db, installment_id=installment_id, new_due_date=body.new_due_date, reason=body.reason, owner_user=actor
    )
    return InstallmentOut.from_model(inst)


@router.get("/credits/{agreement_id}", response_model=CreditResponse)
async def get_credit(agreement_id: uuid.UUID, db: DbSession, _: ViewCredits):
    agreement = await repository.get_agreement(db, agreement_id)
    if agreement is None:
        raise NotFoundError("Crédito no encontrado")
    return CreditResponse.from_model(agreement)


@router.get("/credits/{agreement_id}/installments", response_model=InstallmentListResponse)
async def credit_installments(agreement_id: uuid.UUID, db: DbSession, _: ViewCredits):
    agreement = await repository.get_agreement(db, agreement_id)
    if agreement is None:
        raise NotFoundError("Crédito no encontrado")
    ordered = sorted(agreement.installments, key=lambda i: i.number)
    return InstallmentListResponse(items=[InstallmentOut.from_model(i) for i in ordered], total=len(ordered))


@router.post("/credits/{agreement_id}/pay-multiple", response_model=dict)
async def pay_multiple(agreement_id: uuid.UUID, body: PayMultipleRequest, db: DbSession, actor: ManageInstallments):
    result = await service.pay_multiple_installments(db, agreement_id=agreement_id, data=body, user=actor)
    return {
        "applied_total": str(result["applied_total"]),
        "payments": [
            {"id": str(p.id), "installment_id": str(p.installment_id), "amount": str(p.amount)}
            for p in result["payments"]
        ],
    }


@router.post("/credits/{agreement_id}/deliver", response_model=CreditResponse)
async def deliver_on_credit(agreement_id: uuid.UUID, db: DbSession, actor: ApproveCredits):
    """Entrega anticipada DELIVERED_ON_CREDIT — solo OWNER (#F05-11)."""
    agreement = await service.deliver_on_credit(db, agreement_id=agreement_id, user=actor)
    return CreditResponse.from_model(agreement)

"""Tarea Celery: recordatorios de cuotas próximas a vencer (#F06-11).

Diaria a las 9 AM. Busca cuotas PENDING con due_date == hoy + 3 días y
encola WhatsApp INSTALLMENT_UPCOMING por cliente. Idempotente vía
idempotency_key `installment-upcoming:{cuota}:{fecha}`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.credit_reminders")

REMINDER_DAYS_AHEAD = 3


async def _run() -> dict[str, object]:
    from sqlalchemy import select

    from app.database.session import AsyncSessionLocal
    from app.modules.credits.domain.models import (
        AgreementStatus,
        CreditAgreement,
        CreditInstallment,
        InstallmentStatus,
    )
    from app.modules.customers.domain.models import Customer
    from app.modules.whatsapp.application.service import send_event

    target = date.today() + timedelta(days=REMINDER_DAYS_AHEAD)
    sent = 0
    skipped_no_phone = 0
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(CreditInstallment, CreditAgreement)
            .join(CreditAgreement, CreditInstallment.agreement_id == CreditAgreement.id)
            .where(
                CreditInstallment.due_date == target,
                CreditInstallment.status == InstallmentStatus.PENDING,
                CreditAgreement.status.in_([AgreementStatus.ACTIVE, AgreementStatus.OVERDUE]),
            )
        )
        for installment, agreement in rows.all():
            customer = await db.get(Customer, agreement.customer_id)
            recipient = (customer.phone_whatsapp or customer.phone) if customer else None
            if not recipient:
                skipped_no_phone += 1
                continue
            name = (
                customer.razon_social
                or " ".join(filter(None, [customer.first_name or "", customer.last_name or ""]))
                or None
            )
            message = await send_event(
                db,
                event_type="INSTALLMENT_UPCOMING",
                recipient=recipient,
                variables={
                    "customer_name": name,
                    "installment_number": installment.number,
                    "amount": str(installment.amount),
                    "due_date": installment.due_date.isoformat(),
                    "credit_code": agreement.code,
                },
                idempotency_key=f"installment-upcoming:{installment.id}:{target.isoformat()}",
            )
            if message is not None:
                sent += 1
        await db.commit()
    return {"reminders_queued": sent, "skipped_no_phone": skipped_no_phone, "due_date": target.isoformat()}


@celery_app.task(name="worker.tasks.credits.send_upcoming_installment_reminders")
def send_upcoming_installment_reminders() -> dict[str, object]:
    result: dict[str, object] = asyncio.run(_run())
    logger.info("Recordatorios de cuotas: %s", result)
    return result

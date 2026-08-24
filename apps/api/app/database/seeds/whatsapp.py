"""Seeds de WhatsApp: templates por defecto, config y mensajes ficticios (#F06-12/#F06-20).

Idempotente: templates se insertan/upsertean por event_type; mensajes solo si
no existen sus idempotency_key.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.whatsapp.domain.models import (
    WhatsAppConfig,
    WhatsAppDeliveryLog,
    WhatsAppMessage,
    WhatsAppTemplate,
)

# (name, event_type, body, variables)
TEMPLATES: list[tuple[str, str, str, list[str]]] = [
    (
        "new_sale",
        "NEW_SALE",
        "Hola {customer_name}! Tu compra de {product_list} por S/{total} ha sido registrada. "
        "Código: {sale_code}. Gracias por preferir Inversiones Hasbun.",
        ["customer_name", "product_list", "total", "sale_code"],
    ),
    (
        "payment_received",
        "PAYMENT_RECEIVED",
        "Hola {customer_name}, recibimos tu pago de S/{amount} del crédito {credit_code}. "
        "¡Gracias por mantenerte al día!",
        ["customer_name", "amount", "credit_code"],
    ),
    (
        "installment_upcoming",
        "INSTALLMENT_UPCOMING",
        "Hola {customer_name}, te recordamos que tu cuota #{installment_number} de S/{amount} "
        "vence el {due_date}. Código de crédito: {credit_code}.",
        ["customer_name", "installment_number", "amount", "due_date", "credit_code"],
    ),
    (
        "installment_overdue",
        "INSTALLMENT_OVERDUE",
        "Hola {customer_name}, tu cuota #{installment_number} del crédito {credit_code} está vencida. "
        "Mora acumulada: S/{mora_amount}. Regulariza tu pago para evitar cargos adicionales.",
        ["customer_name", "installment_number", "credit_code", "mora_amount"],
    ),
    (
        "mora_created",
        "MORA_CREATED",
        "Hola {customer_name}, se generó una mora de S/{mora_amount} en el crédito {credit_code} "
        "(período {period}). Capital pendiente: S/{amount}.",
        ["customer_name", "mora_amount", "credit_code", "period", "amount"],
    ),
    (
        "repair_created",
        "REPAIR_CREATED",
        "Hola {customer_name}, registramos tu equipo {device_brand} {device_model} para revisión. "
        "Orden: {repair_code}. Te avisaremos con el diagnóstico.",
        ["customer_name", "device_brand", "device_model", "repair_code"],
    ),
    (
        "repair_ready",
        "REPAIR_READY",
        "Hola {customer_name}! Tu equipo {device_brand} {device_model} está listo. "
        "Orden: {repair_code}. Puedes pasar a recogerlo. Costo: S/{total}.",
        ["customer_name", "device_brand", "device_model", "repair_code", "total"],
    ),
    (
        "quote_created",
        "QUOTE_CREATED",
        "Hola {customer_name}! Te enviamos la cotización {quote_code} por S/{total}, "
        "válida hasta el {valid_until}. Revísala y responde desde este enlace.",
        ["customer_name", "quote_code", "total", "valid_until"],
    ),
    (
        "quote_accepted",
        "QUOTE_ACCEPTED",
        "El cliente {customer_name} aceptó la cotización {quote_code} por S/{total}. "
        "Procede a convertir en venta.",
        ["customer_name", "quote_code", "total"],
    ),
    (
        "installation_created",
        "INSTALLATION_CREATED",
        "Hola {customer_name}, tu instalación quedó programada para el {scheduled_date}. "
        "Orden: {installation_code}. Nuestro técnico te contactará.",
        ["customer_name", "scheduled_date", "installation_code"],
    ),
    (
        "installation_upcoming",
        "INSTALLATION_UPCOMING",
        "Hola {customer_name}, recordatorio: tu instalación {installation_code} es mañana {scheduled_date}.",
        ["customer_name", "installation_code", "scheduled_date"],
    ),
    (
        "stock_low",
        "STOCK_LOW",
        "[INTERNO] Producto {sku} ({product_name}) con stock bajo: quedan {available} unidades "
        "(mínimo {stock_minimum}).",
        ["sku", "product_name", "available", "stock_minimum"],
    ),
    (
        "stock_out",
        "STOCK_OUT",
        "[INTERNO] Producto AGOTADO: {sku} ({product_name}). Reposición urgente requerida.",
        ["sku", "product_name"],
    ),
    (
        "warranty_expiring",
        "WARRANTY_EXPIRING",
        "Hola {customer_name}, la garantía de tu {product_name} (código {warranty_code}) "
        "vence el {expires_at}. Si notas algún detalle, tráelo antes de esa fecha.",
        ["customer_name", "product_name", "warranty_code", "expires_at"],
    ),
    (
        "sale_completed",
        "SALE_COMPLETED",
        "Hola {customer_name}! Has terminado de pagar tu crédito {credit_code} por un total de "
        "S/{total}. ¡Gracias por tu puntualidad! Inversiones Hasbun.",
        ["customer_name", "credit_code", "total"],
    ),
]


async def seed_whatsapp(db: AsyncSession) -> dict[str, int]:
    """Upsert de templates + config + 5 mensajes ficticios. Idempotente."""
    created_templates = 0
    for name, event_type, body, variables in TEMPLATES:
        row = (
            await db.execute(select(WhatsAppTemplate).where(WhatsAppTemplate.event_type == event_type))
        ).scalars().first()
        if row is None:
            db.add(
                WhatsAppTemplate(
                    name=name, event_type=event_type, body=body, variables=variables, active=True
                )
            )
            created_templates += 1
        elif not row.body:
            row.body = body
            row.variables = variables
    await db.flush()

    if (await db.execute(select(WhatsAppConfig).limit(1))).scalars().first() is None:
        db.add(WhatsAppConfig(enabled=True, provider="mock"))

    # --- #F06-20: 5 mensajes ficticios en estados varios ---
    template_by_event = {
        t.event_type: t
        for t in (await db.execute(select(WhatsAppTemplate))).scalars().all()
    }
    now = datetime.now(UTC)
    samples = [
        ("new-sale:seed-1", "NEW_SALE", "51987654321", "SENT"),
        ("payment-received:seed-2", "PAYMENT_RECEIVED", "51987654322", "SENT"),
        ("quote-created:seed-3", "QUOTE_CREATED", "51987654323", "PENDING"),
        ("installment-overdue:seed-4", "INSTALLMENT_OVERDUE", "51987654324", "FAILED"),
        ("stock-low:seed-5", "STOCK_LOW", "51900000001", "FAILED"),
    ]
    created_messages = 0
    for key, event, recipient, status in samples:
        exists = (
            await db.execute(select(WhatsAppMessage).where(WhatsAppMessage.idempotency_key == key))
        ).scalar_one_or_none()
        if exists is not None:
            continue
        template = template_by_event.get(event)
        if template is None:
            continue
        vars_ = {
            "customer_name": "Cliente Seed",
            "sale_code": "VTA-SEED-00001",
            "credit_code": "CRD-SEED-00001",
            "quote_code": "COT-SEED-00001",
            "installment_number": 1,
            "amount": "250.00",
            "mora_amount": "7.50",
            "due_date": now.date().isoformat(),
            "period": f"{now.year:04d}-{now.month:02d}",
            "product_list": "Producto demo",
            "sku": "PRD-00001",
            "product_name": "Producto demo",
            "available": 2,
            "stock_minimum": 5,
        }
        rendered = template.body
        for k, v in vars_.items():
            rendered = rendered.replace("{" + k + "}", str(v))
        message = WhatsAppMessage(
            recipient=recipient,
            template_id=template.id,
            payload={
                "template": template.name,
                "event_type": event,
                "variables": vars_,
                "rendered": rendered,
            },
            status=status,
            idempotency_key=key,
            retry_count=3 if status == "FAILED" else 0,
            error="mock simulated failure (seed)" if status == "FAILED" else None,
            sent_at=now - timedelta(hours=1) if status == "SENT" else None,
            provider_message_id=f"mock-seed-{key}" if status == "SENT" else None,
            next_retry_at=None,
        )
        db.add(message)
        await db.flush()
        if status == "FAILED":
            for attempt in range(1, 4):
                db.add(
                    WhatsAppDeliveryLog(
                        message_id=message.id,
                        attempt_number=attempt,
                        status="FAILED",
                        provider_response={"provider": "mock"},
                        attempted_at=now - timedelta(minutes=60 - attempt * 20),
                        error="mock simulated failure (seed)",
                    )
                )
        created_messages += 1

    await db.commit()
    return {
        "templates_created": created_templates,
        "templates_total": len(TEMPLATES),
        "messages_created": created_messages,
    }

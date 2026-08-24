"""Router del panel de WhatsApp (#F06-13): mensajes, reintento, templates, config."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.users.domain.models import User
from app.modules.whatsapp.application import service as wa_service
from app.modules.whatsapp.domain.models import (
    WhatsAppConfig,
    WhatsAppEventType,
    WhatsAppMessage,
    WhatsAppTemplate,
)
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

ManageWhatsApp = Annotated[User, Depends(require_permission("whatsapp.gestionar"))]
EditConfig = Annotated[User, Depends(require_permission("configuracion.editar"))]


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    event_type: str
    body: str
    variables: list[Any] = []
    active: bool


class TemplateUpdate(BaseModel):
    body: str | None = None
    active: bool | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient: str
    event_type: str
    template_name: str
    rendered: str
    status: str
    retry_count: int
    error: str | None = None
    provider_message_id: str | None = None
    sent_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, m: WhatsAppMessage) -> MessageOut:
        return cls(
            id=m.id,
            recipient=m.recipient,
            event_type=str(m.payload.get("event_type", "")),
            template_name=str(m.payload.get("template", "")),
            rendered=str(m.payload.get("rendered", "")),
            status=m.status,
            retry_count=m.retry_count,
            error=m.error,
            provider_message_id=m.provider_message_id,
            sent_at=m.sent_at,
            created_at=m.created_at,
        )


class MessageListResponse(BaseModel):
    items: list[MessageOut]
    total: int


@router.get("/messages", response_model=MessageListResponse)
async def list_messages(
    db: DbSession,
    _: ManageWhatsApp,
    status: str | None = Query(None),
    event_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    from sqlalchemy import func

    q = select(WhatsAppMessage)
    if status:
        q = q.where(WhatsAppMessage.status == status)
    if event_type:
        # filtrar por evento dentro del payload JSONB
        q = q.where(WhatsAppMessage.payload["event_type"].astext == event_type)
    total = (
        await db.execute(select(func.count()).select_from(q.order_by(None).subquery()))
    ).scalar_one()
    rows = await db.execute(
        q.order_by(WhatsAppMessage.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return MessageListResponse(
        items=[MessageOut.from_model(m) for m in rows.scalars().all()], total=int(total)
    )


@router.post("/messages/{message_id}/retry", response_model=MessageOut)
async def retry_message(message_id: uuid.UUID, db: DbSession, _: ManageWhatsApp):
    """Reintento manual de un mensaje FAILED."""
    message = await wa_service.retry_failed(db, message_id)
    fresh = await db.get(WhatsAppMessage, message.id)
    if fresh is None:
        raise NotFoundError("Mensaje no encontrado")
    return MessageOut.from_model(fresh)


@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(db: DbSession, _: ManageWhatsApp):
    rows = await db.execute(select(WhatsAppTemplate).order_by(WhatsAppTemplate.event_type))
    return [TemplateOut.model_validate(t) for t in rows.scalars().all()]


@router.put("/templates/{template_id}", response_model=TemplateOut)
async def update_template(template_id: uuid.UUID, body: TemplateUpdate, db: DbSession, _: EditConfig):
    """Editar plantilla — solo OWNER (configuracion.editar) (#F06-12)."""
    template = await db.get(WhatsAppTemplate, template_id)
    if template is None:
        raise NotFoundError("Plantilla no encontrada")
    if body.body is not None:
        template.body = body.body
    if body.active is not None:
        template.active = body.active
    await db.commit()
    return TemplateOut.model_validate(template)


@router.get("/events", response_model=list[str])
async def list_events(_: ManageWhatsApp):
    """Catálogo de eventos disponibles para filtros del panel."""
    return sorted(WhatsAppEventType.ALL)


@router.get("/config", response_model=dict)
async def get_config(db: DbSession, _: ManageWhatsApp):
    from app.core.config import settings as app_settings

    enabled = await wa_service.module_enabled(db)
    row = (await db.execute(select(WhatsAppConfig).limit(1))).scalars().first()
    return {
        "enabled": enabled,
        "provider": row.provider if row else app_settings.WHATSAPP_PROVIDER,
    }


@router.put("/config", response_model=dict)
async def set_config(db: DbSession, actor: EditConfig, enabled: bool = Query(...)):
    """Switch on/off del módulo — solo OWNER."""
    from app.core.config import settings as app_settings

    row = (await db.execute(select(WhatsAppConfig).limit(1))).scalars().first()
    if row is None:
        row = WhatsAppConfig(enabled=enabled, provider=app_settings.WHATSAPP_PROVIDER)
        db.add(row)
    else:
        row.enabled = enabled
    await db.commit()
    return {"enabled": row.enabled, "provider": row.provider}

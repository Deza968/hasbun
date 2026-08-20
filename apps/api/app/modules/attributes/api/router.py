"""Router de atributos dinámicos (#F02-04)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.attributes.application import service
from app.modules.attributes.application.schemas import (
    AttributeCreate,
    AttributeResponse,
    AttributeValueCreate,
    AttributeValueResponse,
)
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends

router = APIRouter(tags=["attributes"])

ManageAttributes = Annotated[
    User, Depends(require_permission("productos.editar"))
]


@router.get("/attributes", response_model=list[AttributeResponse])
async def list_attributes(db: DbSession) -> list[AttributeResponse]:
    attrs = await service.list_attributes(db)
    return [
        AttributeResponse(
            id=a.id, name=a.name, data_type=a.data_type, unit=a.unit, created_at=a.created_at
        )
        for a in attrs
    ]


@router.post("/attributes", response_model=AttributeResponse, status_code=201)
async def create_attribute(
    body: AttributeCreate,
    db: DbSession,
    _: ManageAttributes,
) -> AttributeResponse:
    attr = await service.create_attribute(
        db, name=body.name, data_type=body.data_type, unit=body.unit
    )
    return AttributeResponse(
        id=attr.id,
        name=attr.name,
        data_type=attr.data_type,
        unit=attr.unit,
        created_at=attr.created_at,
    )


@router.get("/attributes/{attribute_id}/values", response_model=list[AttributeValueResponse])
async def list_attribute_values(
    attribute_id: uuid.UUID,
    db: DbSession,
) -> list[AttributeValueResponse]:
    values = await service.list_attribute_values(db, attribute_id=attribute_id)
    return [
        AttributeValueResponse(id=v.id, attribute_id=v.attribute_id, value=v.value)
        for v in values
    ]


@router.post(
    "/attributes/{attribute_id}/values",
    response_model=AttributeValueResponse,
    status_code=201,
)
async def add_attribute_value(
    attribute_id: uuid.UUID,
    body: AttributeValueCreate,
    db: DbSession,
    _: ManageAttributes,
) -> AttributeValueResponse:
    av = await service.add_attribute_value(
        db, attribute_id=attribute_id, value=body.value
    )
    return AttributeValueResponse(id=av.id, attribute_id=av.attribute_id, value=av.value)

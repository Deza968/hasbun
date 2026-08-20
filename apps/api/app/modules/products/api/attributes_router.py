"""Router de atributos dinámicos."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.products.application.schemas import (
    AttributeCreate,
    AttributeResponse,
    AttributeValueCreate,
    AttributeValueResponse,
)
from app.modules.products.application.service import (
    add_attribute_value,
    create_attribute,
)
from app.modules.products.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends

router = APIRouter(tags=["attributes"])

ManageAttributes = Annotated[User, Depends(require_permission("productos.editar"))]


def _to_response(attribute) -> AttributeResponse:
    return AttributeResponse(
        id=attribute.id,
        name=attribute.name,
        data_type=attribute.data_type,
        unit=attribute.unit,
        values=[
            AttributeValueResponse(id=v.id, attribute_id=v.attribute_id, value=v.value)
            for v in attribute.values
        ],
    )


@router.get("/attributes", response_model=list[AttributeResponse])
async def list_attributes(
    db: DbSession,
) -> list[AttributeResponse]:
    """Lista atributos del sistema."""
    attributes = await repository.list_attributes(db)
    return [_to_response(a) for a in attributes]


@router.post("/attributes", response_model=AttributeResponse, status_code=201)
async def create_attribute_endpoint(
    body: AttributeCreate,
    db: DbSession,
    actor: ManageAttributes,
) -> AttributeResponse:
    """Crea un atributo (solo OWNER)."""
    attribute = await create_attribute(db, data=body, created_by=actor)
    return _to_response(attribute)


@router.get("/attributes/{attribute_id}/values", response_model=list[AttributeValueResponse])
async def list_attribute_values(
    attribute_id: uuid.UUID,
    db: DbSession,
) -> list[AttributeValueResponse]:
    """Lista los valores de un atributo."""
    from app.core.exceptions import NotFoundError

    attribute = await repository.get_attribute_by_id(db, attribute_id)
    if attribute is None:
        raise NotFoundError("Atributo no encontrado")
    return [
        AttributeValueResponse(id=v.id, attribute_id=v.attribute_id, value=v.value)
        for v in attribute.values
    ]


@router.post(
    "/attributes/{attribute_id}/values",
    response_model=AttributeValueResponse,
    status_code=201,
)
async def add_attribute_value_endpoint(
    attribute_id: uuid.UUID,
    body: AttributeValueCreate,
    db: DbSession,
    actor: ManageAttributes,
) -> AttributeValueResponse:
    """Agrega un valor a un atributo (solo OWNER)."""
    value = await add_attribute_value(
        db, attribute_id=attribute_id, value=body.value, created_by=actor
    )
    return AttributeValueResponse(id=value.id, attribute_id=value.attribute_id, value=value.value)

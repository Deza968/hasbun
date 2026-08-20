"""Schemas del módulo de atributos."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AttributeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    data_type: str = Field("text", pattern="^(text|number|boolean|list)$")
    unit: str | None = Field(default=None, max_length=50)


class AttributeResponse(BaseModel):
    id: uuid.UUID
    name: str
    data_type: str
    unit: str | None
    created_at: datetime


class AttributeValueCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=200)


class AttributeValueResponse(BaseModel):
    id: uuid.UUID
    attribute_id: uuid.UUID
    value: str

"""Schemas del módulo de marcas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    logo_file_id: uuid.UUID | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    logo_file_id: uuid.UUID | None = None
    active: bool | None = None


class BrandResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_file_id: uuid.UUID | None = None
    active: bool
    created_at: datetime

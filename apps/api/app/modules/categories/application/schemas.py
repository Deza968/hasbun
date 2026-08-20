"""Schemas del módulo de categorías."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    parent_id: uuid.UUID | None = None
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    parent_id: uuid.UUID | None = None
    description: str | None = None
    active: bool | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None = None
    description: str | None = None
    active: bool
    created_at: datetime


class CategoryTreeResponse(CategoryResponse):
    children: list[CategoryTreeResponse] = []

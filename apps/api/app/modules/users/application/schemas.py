"""Schemas del módulo de usuarios."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(..., min_length=8)
    role_codes: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    phone: str | None = None
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None = None
    created_at: datetime
    roles: list[str] = []


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class AssignRoleRequest(BaseModel):
    role_code: str


class AssignPermissionRequest(BaseModel):
    codename: str
    granted: bool
    reason: str | None = None

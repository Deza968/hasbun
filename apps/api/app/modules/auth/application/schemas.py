"""Schemas de autenticación."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["owner@hasbun.dev"])
    password: str = Field(..., min_length=1, examples=["Owner2026!"])


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str
    phone: str | None = None
    is_active: bool
    is_superuser: bool
    roles: list[str]
    permissions: list[str]

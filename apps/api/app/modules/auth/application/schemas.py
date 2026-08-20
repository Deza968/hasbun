"""Schemas de autenticación."""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_PATTERN = r"^(?=.*[A-Z])(?=.*\d).{8,}$"  # noqa: S105
PASSWORD_MESSAGE = "La contraseña debe tener al menos 8 caracteres, una mayúscula y un número"  # noqa: S105


def validate_password_strength(value: str) -> str:
    if not re.match(PASSWORD_PATTERN, value):
        raise ValueError(PASSWORD_MESSAGE)
    return value


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["owner@hasbun.dev"])
    password: str = Field(..., min_length=1, examples=["Owner2026!"])


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, examples=["NuevaPass2026!"])

    _validate_password = field_validator("new_password")(validate_password_strength)


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

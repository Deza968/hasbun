"""Modelo de dominio del usuario."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.files.domain.models import FileObject
    from app.modules.permissions.domain.models import UserPermissionOverride
    from app.modules.roles.domain.models import Role


class User(BaseModel, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        primaryjoin="User.id == user_roles.c.user_id",
        secondaryjoin="user_roles.c.role_id == Role.id",
        lazy="selectin",
    )
    permission_overrides: Mapped[list[UserPermissionOverride]] = relationship(
        "UserPermissionOverride",
        back_populates="user",
        foreign_keys="UserPermissionOverride.user_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    files: Mapped[list[FileObject]] = relationship(
        "FileObject",
        back_populates="uploader",
        foreign_keys="FileObject.uploaded_by",
        lazy="selectin",
    )

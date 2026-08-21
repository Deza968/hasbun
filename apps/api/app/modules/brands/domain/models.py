"""Modelo de marca (#F02-03)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.files.domain.models import FileObject


class Brand(BaseModel, Base):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    logo_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    logo: Mapped[FileObject | None] = relationship(
        "FileObject", foreign_keys=[logo_file_id], lazy="selectin"
    )

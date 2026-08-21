"""Modelo de archivo almacenado (S3/MinIO) (#F02-10)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.users.domain.models import User


class FileObject(BaseModel, Base):
    __tablename__ = "file_objects"

    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    uploader: Mapped[User | None] = relationship(
        "User", foreign_keys=[uploaded_by], lazy="selectin"
    )

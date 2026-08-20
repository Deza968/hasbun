"""Modelo de dominio de objetos de archivo (FileObject)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.users.domain.models import User


class FileObject(BaseModel, Base):
    __tablename__ = "file_objects"

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    uploader: Mapped[User | None] = relationship(
        "User", back_populates="files", lazy="selectin"
    )

"""Servicio de archivos (#F02-10): validación MIME real, checksum, MinIO, FileObject."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.modules.audit.application.service import log
from app.modules.files.domain.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    StorageError,
)
from app.modules.files.domain.models import FileObject
from app.modules.files.infrastructure.storage import build_storage
from app.modules.users.domain.models import User
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession


def _detect_mime(data: bytes) -> str:
    """Detecta el tipo MIME real del contenido (no confía en la extensión)."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    return "application/octet-stream"


async def upload_file(
    db: AsyncSession, *, file: UploadFile, user: User
) -> FileObject:
    """Valida MIME/checksum, sube a S3 y registra FileObject."""
    raw = await file.read()
    if len(raw) > settings.FILE_MAX_SIZE_BYTES:
        raise FileTooLargeError(
            "El archivo excede el tamaño máximo permitido",
            max_size=settings.FILE_MAX_SIZE_BYTES,
        )

    detected = _detect_mime(raw)
    if detected not in settings.FILE_ALLOWED_MIME_TYPES:
        raise InvalidFileTypeError(
            f"Tipo de archivo no permitido (detectado: {detected})"
        )

    checksum = hashlib.sha256(raw).hexdigest()
    file_id = uuid.uuid4()
    extension = detected.split("/")[-1] or "bin"
    storage_key = f"uploads/{file_id}.{extension}"

    provider = build_storage()
    try:
        await provider.upload(
            storage_key=storage_key, data=raw, mime_type=detected
        )
    except RuntimeError as exc:
        raise StorageError(str(exc)) from exc

    obj = FileObject(
        id=file_id,
        storage_key=storage_key,
        bucket=provider.bucket,
        original_name=file.filename or "archivo",
        mime_type=detected,
        size=len(raw),
        checksum=checksum,
        metadata_={"uploaded_at": datetime.now(UTC).isoformat()},
        uploaded_by=user.id,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    await log(
        action="UPLOAD_FILE",
        module="files",
        user_id=user.id,
        entity_type="FileObject",
        entity_id=obj.id,
        new_values={
            "original_name": obj.original_name,
            "mime_type": obj.mime_type,
            "size": obj.size,
        },
    )
    return obj


async def get_file_url(db: AsyncSession, *, file_id: uuid.UUID) -> str:
    obj = await db.get(FileObject, file_id)
    if obj is None or obj.deleted_at is not None:
        raise NotFoundError("Archivo no encontrado")
    provider = build_storage()
    try:
        return await provider.get_url(
            obj.storage_key, ttl_seconds=settings.FILE_SIGNED_URL_TTL_SECONDS
        )
    except RuntimeError as exc:
        raise StorageError(str(exc)) from exc


async def delete_file(db: AsyncSession, *, file_id: uuid.UUID, user: User) -> FileObject:
    """Soft delete: marca deleted_at y elimina el objeto del bucket."""
    obj = await db.get(FileObject, file_id)
    if obj is None:
        raise NotFoundError("Archivo no encontrado")
    provider = build_storage()
    try:
        await provider.delete(obj.storage_key)
    except RuntimeError:
        # No bloquear si el objeto ya no existe en el bucket
        pass
    obj.deleted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(obj)
    await log(
        action="DELETE_FILE",
        module="files",
        user_id=user.id,
        entity_type="FileObject",
        entity_id=obj.id,
        new_values={"deleted_at": obj.deleted_at.isoformat()},
    )
    return obj


async def get_file_object(db: AsyncSession, *, file_id: uuid.UUID) -> FileObject:
    obj = await db.get(FileObject, file_id)
    if obj is None:
        raise NotFoundError("Archivo no encontrado")
    return obj

"""Servicios del módulo de archivos."""

from __future__ import annotations

import hashlib
import uuid

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.audit.application.service import log
from app.modules.files.domain.models import FileObject
from app.modules.files.infrastructure import repository, storage
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def detect_mime(data: bytes) -> str:
    """Detecta el MIME real por magic bytes (no confía en la extensión)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"GIF8":
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def validate_upload(data: bytes, size: int) -> str:
    if size <= 0:
        raise ValidationError("El archivo está vacío")
    if size > MAX_UPLOAD_SIZE:
        raise ValidationError("El archivo supera el tamaño máximo de 10 MB")
    mime = detect_mime(data)
    if mime not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Solo se permiten imágenes reales (JPEG, PNG, WebP, GIF)")
    return mime


async def upload_file(
    db: AsyncSession,
    *,
    filename: str,
    data: bytes,
    mime_type: str | None,
    uploaded_by: User,
) -> FileObject:
    del mime_type  # el MIME se valida del contenido real, no del declarado
    mime = validate_upload(data, len(data))

    key = f"uploads/{uuid.uuid4().hex}"
    await storage.upload_bytes(key, data, mime)

    file_obj = FileObject(
        storage_key=key,
        bucket=storage.get_storage().bucket,
        original_name=filename,
        mime_type=mime,
        size=len(data),
        checksum=hashlib.sha256(data).hexdigest(),
        uploaded_by=uploaded_by.id,
    )
    file_obj = await repository.create(db, file_obj)
    await log(
        action="UPLOAD_FILE",
        module="files",
        user_id=uploaded_by.id,
        entity_type="FileObject",
        entity_id=file_obj.id,
        new_values={
            "filename": filename,
            "mime_type": mime,
            "size": len(data),
        },
    )
    return file_obj


async def get_file(db: AsyncSession, file_id: uuid.UUID) -> FileObject:
    file_obj = await repository.get_by_id(db, file_id)
    if file_obj is None or file_obj.is_deleted:
        raise NotFoundError("Archivo no encontrado")
    return file_obj


async def download_bytes(db: AsyncSession, file_id: uuid.UUID) -> tuple[bytes, FileObject]:
    file_obj = await get_file(db, file_id)
    data = await storage.get_bytes(file_obj.storage_key)
    return data, file_obj


async def delete_file(
    db: AsyncSession, *, file_id: uuid.UUID, deleted_by: User
) -> None:
    file_obj = await get_file(db, file_id)
    await storage.delete_object(file_obj.storage_key)
    await repository.mark_deleted(db, file_id)
    await log(
        action="DELETE_FILE",
        module="files",
        user_id=deleted_by.id,
        entity_type="FileObject",
        entity_id=file_id,
        old_values={"storage_key": file_obj.storage_key, "original_name": file_obj.original_name},
    )

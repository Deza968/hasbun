"""Router de archivos (#F02-10)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user
from app.modules.files.application import service
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, UploadFile

router = APIRouter(tags=["files"])

CurrentUser = Annotated[User, Depends(get_current_active_user)]


@router.post("/files/upload")
async def upload_file(
    file: UploadFile,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, object]:
    """Sube un archivo a MinIO y registra el FileObject (autenticado)."""
    obj = await service.upload_file(db, file=file, user=user)
    return {
        "id": str(obj.id),
        "original_name": obj.original_name,
        "mime_type": obj.mime_type,
        "size": obj.size,
        "checksum": obj.checksum,
    }


@router.get("/files/{file_id}/url")
async def get_file_url(
    file_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, str]:
    """URL firmada con TTL configurado."""
    url = await service.get_file_url(db, file_id=file_id)
    return {"url": url}


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict[str, str]:
    """Soft delete del archivo (y borrado del bucket)."""
    await service.delete_file(db, file_id=file_id, user=user)
    return {"message": "Archivo eliminado"}

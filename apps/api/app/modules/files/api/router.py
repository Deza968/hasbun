"""Router de archivos (upload/download/delete vía MinIO)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.files.application.schemas import FileResponse
from app.modules.files.application.service import delete_file, download_bytes, upload_file
from app.modules.files.domain.models import FileObject
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response

router = APIRouter(tags=["files"])

UploadFiles = Annotated[User, Depends(require_permission("archivos.subir"))]
DeleteFiles = Annotated[User, Depends(require_permission("archivos.eliminar"))]


def _to_response(file: FileObject) -> FileResponse:
    return FileResponse(
        id=file.id,
        original_name=file.original_name,
        mime_type=file.mime_type,
        size=file.size,
        checksum=file.checksum,
        created_at=file.created_at,
    )


@router.post("/files/upload", response_model=FileResponse, status_code=201)
async def upload_endpoint(
    file: UploadFile,
    db: DbSession,
    actor: UploadFiles,
) -> FileResponse:
    """Sube una imagen a MinIO (solo OWNER)."""
    data = await file.read()
    try:
        name = file.filename or "archivo"
    finally:
        await file.close()
    file_obj = await upload_file(
        db,
        filename=name,
        data=data,
        mime_type=file.content_type,
        uploaded_by=actor,
    )
    return _to_response(file_obj)


@router.get("/files/{file_id}/download")
async def download_endpoint(
    file_id: uuid.UUID,
    db: DbSession,
) -> Response:
    """Descarga el contenido de un archivo."""
    data, file_obj = await download_bytes(db, file_id)
    return Response(
        content=data,
        media_type=file_obj.mime_type,
        headers={"Content-Disposition": f'inline; filename="{file_obj.original_name}"'},
    )


@router.delete("/files/{file_id}", status_code=204)
async def delete_endpoint(
    file_id: uuid.UUID,
    db: DbSession,
    actor: DeleteFiles,
) -> None:
    """Elimina un archivo de MinIO (solo OWNER)."""
    await delete_file(db, file_id=file_id, deleted_by=actor)

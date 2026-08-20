"""Schemas del módulo de archivos."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    mime_type: str
    size: int
    checksum: str
    created_at: datetime

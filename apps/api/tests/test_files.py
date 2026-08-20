"""Tests del módulo de archivos (#F02-20).

Nota: los tests de subida requieren MinIO o un stub. Para no depender de
infra, se testea la lógica de validación MIME y checksum con un proveedor
mock, y la integración del endpoint se omite si no hay S3 configurado.
"""

from __future__ import annotations

import hashlib

import httpx
import pytest
from app.core.config import settings


def _jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0fake-jpeg-data"


def _exe_disguised_as_jpg() -> bytes:
    return b"MZ\x90\x00fake-exe-not-jpeg"


async def test_detect_mime_rejects_disguised_exe(client: httpx.AsyncClient) -> None:
    from app.modules.files.application.service import _detect_mime

    assert _detect_mime(_exe_disguised_as_jpg()) != "image/jpeg"
    assert _detect_mime(_jpeg_bytes()) == "image/jpeg"
    assert _detect_mime(b"%PDF-1.4 fake pdf") == "application/pdf"


async def test_upload_valid_jpeg_creates_file_object(
    client: httpx.AsyncClient, monkeypatch
) -> None:
    """Sube un jpeg válido con un proveedor de almacenamiento falso."""
    from app.modules.files.domain.storage import StorageProvider

    calls: list[tuple[str, bytes, str]] = []

    class FakeStorage(StorageProvider):
        bucket = "test"

        async def upload(self, *, storage_key, data, mime_type) -> None:
            calls.append((storage_key, data, mime_type))

        async def get_url(self, storage_key, *, ttl_seconds) -> str:
            return f"https://s3.test/{storage_key}?expires={ttl_seconds}"

        async def delete(self, storage_key) -> None:
            pass

    monkeypatch.setattr(
        "app.modules.files.application.service.build_storage",
        lambda: FakeStorage(),
    )

    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "Owner2026!"},
    )
    response = await client.post(
        "/api/v1/files/upload",
        files={"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["mime_type"] == "image/jpeg"
    assert data["checksum"] == hashlib.sha256(_jpeg_bytes()).hexdigest()
    assert len(calls) == 1
    assert calls[0][1] == _jpeg_bytes()


async def test_upload_invalid_mime_rejected(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "Owner2026!"},
    )
    # Disfrazado como jpg pero es un .exe
    response = await client.post(
        "/api/v1/files/upload",
        files={"file": ("virus.exe", _exe_disguised_as_jpg(), "image/jpeg")},
    )
    assert response.status_code == 400


async def test_upload_exceeds_size_limit(client: httpx.AsyncClient) -> None:
    from app.modules.files.application.service import _detect_mime, upload_file
    from app.modules.files.domain.exceptions import FileTooLargeError

    big = b"\xff\xd8\xff\xe0" + b"\x00" * (settings.FILE_MAX_SIZE_BYTES + 1)
    assert _detect_mime(big) == "image/jpeg"

    with pytest.raises(FileTooLargeError) as exc:

        class FakeUpload:
            filename = "big.jpg"

            async def read(self) -> bytes:
                return big

        from app.modules.users.domain.models import User

        await upload_file(
            None,  # type: ignore[arg-type]
            file=FakeUpload(),  # type: ignore[arg-type]
            user=User(email="x@x.com", username="x", full_name="X", password_hash="x"),
        )
    assert exc.value.status_code == 413


async def test_checksum_matches(client: httpx.AsyncClient, monkeypatch) -> None:
    from app.modules.files.domain.storage import StorageProvider

    class FakeStorage(StorageProvider):
        bucket = "test"

        async def upload(self, *, storage_key, data, mime_type) -> None:
            pass

        async def get_url(self, storage_key, *, ttl_seconds) -> str:
            return f"https://s3.test/{storage_key}"

        async def delete(self, storage_key) -> None:
            pass

    monkeypatch.setattr(
        "app.modules.files.application.service.build_storage",
        lambda: FakeStorage(),
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@hasbun.dev", "password": "Owner2026!"},
    )
    response = await client.post(
        "/api/v1/files/upload",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake pdf", "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["checksum"] == hashlib.sha256(b"%PDF-1.4 fake pdf").hexdigest()

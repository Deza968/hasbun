"""Tests del módulo de archivos (#F02-20)."""

from __future__ import annotations

import io
import zipfile

import httpx

OWNER = {"email": "owner@hasbun.dev", "password": "Owner2026!"}


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json=OWNER)
    assert response.status_code == 200


async def _upload(client: httpx.AsyncClient, filename: str, content: bytes, mime: str):
    files = {"file": (filename, io.BytesIO(content), mime)}
    return await client.post("/api/v1/files/upload", files=files)


async def test_upload_valid_jpeg(client: httpx.AsyncClient, monkeypatch) -> None:
    bucket = {"bucket": "hasbun-test"}

    async def fake_upload_bytes(key: str, data: bytes, mime_type: str) -> None:
        bucket[key] = data

    async def fake_get_bytes(key: str) -> bytes:
        return bucket[key]

    async def fake_delete(key: str) -> None:
        bucket.pop(key, None)

    class FakeStorage:
        bucket = "hasbun-test"

    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.upload_bytes", fake_upload_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_bytes", fake_get_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.delete_object", fake_delete
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_storage",
        lambda: FakeStorage(),
    )

    await _login(client)
    content = b"\xff\xd8\xff\xe0fakejpegdata"
    response = await _upload(client, "foto.jpg", content, "image/jpeg")
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["mime_type"] == "image/jpeg"
    assert data["original_name"] == "foto.jpg"
    assert data["size"] == len(content)
    assert len(data["checksum"]) == 64  # SHA-256 hex

    download = await client.get(f"/api/v1/files/{data['id']}/download")
    assert download.status_code == 200
    assert download.content == content


async def test_upload_invalid_mime_disguised_as_jpg(
    client: httpx.AsyncClient, monkeypatch
) -> None:
    async def fake_upload_bytes(key: str, data: bytes, mime_type: str) -> None:
        raise AssertionError("no debería subirse")

    async def fake_get_bytes(key: str) -> bytes:
        raise AssertionError("no debería leerse")

    async def fake_delete(key: str) -> None:
        raise AssertionError("no debería eliminarse")

    class FakeStorage:
        bucket = "hasbun-test"

    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.upload_bytes", fake_upload_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_bytes", fake_get_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.delete_object", fake_delete
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_storage",
        lambda: FakeStorage(),
    )

    await _login(client)
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("malware.exe", b"evil")
    response = await _upload(
        client, "foto.jpg", zip_bytes.getvalue(), "image/jpeg"
    )
    assert response.status_code == 422


async def test_upload_oversized_rejected(client: httpx.AsyncClient, monkeypatch) -> None:
    class FakeStorage:
        bucket = "hasbun-test"

    async def fake_upload_bytes(key: str, data: bytes, mime_type: str) -> None:
        raise AssertionError("no debería subirse")

    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.upload_bytes", fake_upload_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_storage",
        lambda: FakeStorage(),
    )

    await _login(client)
    big = b"x" * (11 * 1024 * 1024)
    response = await _upload(client, "grande.jpg", big, "image/jpeg")
    assert response.status_code == 422


async def test_checksum_matches(client: httpx.AsyncClient, monkeypatch) -> None:
    import hashlib

    content = b"\xff\xd8\xff\xe0fakejpegdata"
    expected = hashlib.sha256(content).hexdigest()

    bucket = {"bucket": "hasbun-test"}

    async def fake_upload_bytes(key: str, data: bytes, mime_type: str) -> None:
        bucket[key] = data

    async def fake_get_bytes(key: str) -> bytes:
        return bucket[key]

    async def fake_delete(key: str) -> None:
        bucket.pop(key, None)

    class FakeStorage:
        bucket = "hasbun-test"

    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.upload_bytes", fake_upload_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_bytes", fake_get_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.delete_object", fake_delete
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_storage",
        lambda: FakeStorage(),
    )

    await _login(client)
    response = await _upload(client, "foto.jpg", content, "image/jpeg")
    assert response.status_code == 201
    assert response.json()["checksum"] == expected


async def test_delete_file_marks_soft_delete(client: httpx.AsyncClient, monkeypatch) -> None:
    bucket: dict[str, bytes] = {}
    deleted: list[str] = []

    async def fake_upload_bytes(key: str, data: bytes, mime_type: str) -> None:
        bucket[key] = data

    async def fake_get_bytes(key: str) -> bytes:
        return bucket[key]

    async def fake_delete(key: str) -> None:
        deleted.append(key)

    class FakeStorage:
        bucket = "hasbun-test"

    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.upload_bytes", fake_upload_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_bytes", fake_get_bytes
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.delete_object", fake_delete
    )
    monkeypatch.setattr(
        "app.modules.files.infrastructure.storage.get_storage",
        lambda: FakeStorage(),
    )

    await _login(client)
    upload = await _upload(client, "foto.jpg", b"\xff\xd8\xff\xe0data", "image/jpeg")
    file_id = upload.json()["id"]

    response = await client.delete(f"/api/v1/files/{file_id}")
    assert response.status_code == 204
    assert len(deleted) == 1

    download = await client.get(f"/api/v1/files/{file_id}/download")
    assert download.status_code == 404

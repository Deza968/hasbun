"""Excepciones del módulo de archivos."""

from __future__ import annotations

from app.core.exceptions import HasbunException


class InvalidFileTypeError(HasbunException):
    status_code = 400
    code = "INVALID_FILE_TYPE"


class FileTooLargeError(HasbunException):
    status_code = 413
    code = "FILE_TOO_LARGE"
    def __init__(self, message: str = "", max_size: int | None = None) -> None:
        super().__init__(message)
        if max_size:
            self.details = {"max_size_bytes": max_size}


class StorageError(HasbunException):
    status_code = 500
    code = "STORAGE_ERROR"

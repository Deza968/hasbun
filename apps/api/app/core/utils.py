"""Utilidades compartidas de la aplicación."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str, max_length: int = 160) -> str:
    """Convierte un texto en slug URL-safe (ASCII, minúsculas, guiones)."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_length].rstrip("-")

"""Shared file-upload helpers.

Files are stored through Django's default storage, which points at local
media in dev/test and Cloudflare R2 in configured environments.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from django.core.files.storage import default_storage
from django.utils.text import slugify


def store_uploaded_file(uploaded_file, *, prefix: str) -> str:
    stem = slugify(Path(uploaded_file.name).stem) or "upload"
    suffix = Path(uploaded_file.name).suffix.lower()
    path = f"{prefix.rstrip('/')}/{uuid4().hex}-{stem}{suffix}"
    saved = default_storage.save(path, uploaded_file)
    url = default_storage.url(saved)
    if url.startswith("/"):
        return f"https://media.layapa.local{url}"
    return url

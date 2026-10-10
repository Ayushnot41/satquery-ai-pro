"""Security utilities — file validation, path sanitization, upload checks."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .config import settings

# Allowed image extensions
ALLOWED_EXTENSIONS = {".tif", ".tiff", ".jp2", ".png", ".jpg", ".jpeg", ".geotiff"}

# Dangerous characters in filenames
UNSAFE_CHARS = re.compile(r"[^\w\-. ]")


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from a filename."""
    name = os.path.basename(filename)
    name = UNSAFE_CHARS.sub("_", name)
    return name[:255]  # Limit length


def validate_file_extension(filename: str) -> bool:
    """Check if the file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Check if the file is within the size limit."""
    return 0 < file_size <= settings.max_upload_bytes


def ensure_safe_path(path: str, base_dir: str | None = None) -> Path:
    """Ensure a path doesn't escape the base directory (path traversal prevention)."""
    base = Path(base_dir or str(settings.upload_path)).resolve()
    resolved = (base / path).resolve()
    if not resolved.is_relative_to(base):
        raise ValueError(f"Path traversal detected: {path}")
    return resolved

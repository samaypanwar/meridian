from __future__ import annotations

from pathlib import Path

from meridian.config import Settings


def save(data: bytes, name: str, *, settings: Settings) -> Path:
    docs_dir = settings.data_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / name
    path.write_bytes(data)
    return path

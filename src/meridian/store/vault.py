from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

from meridian.config import Settings


def planned_extraction_path(
    slug: str,
    *,
    settings: Settings,
    on_date: date | None = None,
) -> Path:
    inbox = settings.capture_path
    day = (on_date or date.today()).isoformat()
    safe_slug = slug.strip().lower().replace(" ", "-")
    return inbox / f"extraction-{day}-{safe_slug}.md"


def write_extraction(
    note_md: str,
    slug: str,
    *,
    settings: Settings,
    on_date: date | None = None,
) -> Path:
    path = planned_extraction_path(slug, settings=settings, on_date=on_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(note_md, encoding="utf-8")
    return path


def iter_extractions(*, settings: Settings) -> Iterable[Path]:
    root = settings.capture_path
    if not root.exists():
        return
    yield from sorted(root.glob("extraction-*.md"))

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

from meridian.config import Settings


def write_extraction(
    note_md: str,
    slug: str,
    *,
    settings: Settings,
    on_date: date | None = None,
) -> Path:
    inbox = settings.vault_path
    inbox.mkdir(parents=True, exist_ok=True)
    day = (on_date or date.today()).isoformat()
    safe_slug = slug.strip().lower().replace(" ", "-")
    filename = f"extraction-{day}-{safe_slug}.md"
    path = inbox / filename
    path.write_text(note_md, encoding="utf-8")
    return path


def iter_extractions(*, settings: Settings) -> Iterable[Path]:
    inbox = settings.vault_path
    if not inbox.exists():
        return
    yield from sorted(inbox.glob("extraction-*.md"))

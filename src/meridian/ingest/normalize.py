from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from meridian.store.models import Source


def detect_type(url_or_path: str) -> str:
    lowered = url_or_path.lower().strip()
    parsed = urlparse(lowered)
    if parsed.path.lower().endswith(".pdf"):
        return "pdf"
    host = parsed.netloc.removeprefix("www.")
    if host in {"arxiv.org", "export.arxiv.org"} or "arxiv.org" in host:
        return "arxiv"
    if host in {"youtube.com", "youtu.be", "m.youtube.com"}:
        return "youtube"
    if parsed.scheme in {"http", "https"}:
        return "web"
    if Path(url_or_path).suffix.lower() == ".pdf":
        return "pdf"
    return "web"


def _genre_for(source_type: str) -> str:
    return {
        "arxiv": "paper",
        "pdf": "paper",
        "youtube": "video",
        "web": "nonfiction",
    }.get(source_type, "nonfiction")


def ingest(ref: str) -> Source:
    source_type = detect_type(ref)
    return Source(
        id=None,
        added_at=datetime.now(timezone.utc).isoformat(),
        url=ref if source_type != "pdf" or ref.startswith("http") else None,
        source_type=source_type,
        genre=_genre_for(source_type),
        title=None,
        author=None,
        length_meta=None,
        blob_path=ref if source_type == "pdf" and not ref.startswith("http") else None,
        normalized_text=None,
        status="queued",
    )

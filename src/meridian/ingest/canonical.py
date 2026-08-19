from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

from meridian.ingest import arxiv as arxiv_mod
from meridian.ingest import lesswrong
from meridian.ingest.normalize import detect_type
from meridian.ingest.transcript import _video_id_from_url

_TRACKING_QUERY_KEYS = frozenset({"fbclid", "ref", "source", "mc_cid", "mc_eid"})


def canonical_ref(ref: str) -> str:
    stripped = ref.strip()
    if not stripped:
        raise ValueError("Empty reference")

    source_type = detect_type(stripped)
    if source_type == "youtube":
        return f"youtube:{_video_id_from_url(stripped)}"

    if lesswrong.is_lesswrong_url(stripped):
        post_id = lesswrong.post_id_from_url(stripped)
        if post_id:
            return f"lesswrong:{post_id}"

    if source_type == "arxiv":
        arxiv_id = arxiv_mod.arxiv_id_from_ref(stripped)
        if arxiv_id:
            return f"arxiv:{arxiv_id}"

    if source_type == "pdf":
        if stripped.lower().startswith(("http://", "https://")):
            return f"pdf:{_normalize_web_url(stripped)}"
        path = Path(stripped).expanduser().resolve()
        return f"pdf:{path}"

    return f"web:{_normalize_web_url(stripped)}"


def _normalize_web_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if not host:
        return url.strip().lower()
    path = parsed.path.rstrip("/") or "/"
    query_parts = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in _TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_parts))
    normalized = f"https://{host}{path}"
    if query:
        normalized = f"{normalized}?{query}"
    return normalized

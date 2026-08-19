from __future__ import annotations

from typing import Any

from meridian.ingest import arxiv as arxiv_mod
from meridian.ingest import lesswrong, pdf, transcript, web
from meridian.ingest.transcript_errors import YouTubeTranscriptBlocked


def fetch_normalized(
    ref: str, source_type: str
) -> tuple[str, dict[str, Any], str | None]:
    if lesswrong.is_lesswrong_url(ref):
        text, meta = lesswrong.fetch_text(ref)
        return text, meta, ref
    if source_type == "web":
        text, meta = web.fetch_text(ref)
        return text, meta, ref
    if source_type == "pdf":
        text, meta = pdf.extract_text(ref)
        return text, meta, ref
    if source_type == "arxiv":
        text, meta = arxiv_mod.fetch_text(ref)
        return text, meta, ref
    if source_type == "youtube":
        try:
            text, meta = transcript.fetch_captions(ref)
            return text, meta, ref
        except YouTubeTranscriptBlocked as exc:
            meta = dict(exc.meta)
            meta["transcript_status"] = exc.reason
            return "", meta, ref
    raise ValueError(f"Unsupported source type: {source_type}")

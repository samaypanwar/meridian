from __future__ import annotations

import json
from typing import Any

from meridian.ingest.fetch import fetch_normalized
from meridian.ingest.titles import clean_extracted_title
from meridian.store.models import Source


def ref_for_source(source: Source) -> str:
    if source.url:
        return source.url
    if source.blob_path:
        return source.blob_path
    raise ValueError("Source has no URL or file path to re-fetch")


def apply_fetched_content(source: Source, ref: str) -> Source:
    text, meta, url = fetch_normalized(ref, source.source_type)
    source.length_meta = json.dumps(meta)
    source.url = url or source.url
    source.title = meta.get("title") or source.title or ref
    if source.title:
        source.title = clean_extracted_title(source.title, source.url or ref)
    source.author = meta.get("author")
    if text.strip():
        source.normalized_text = text
    elif source.source_type == "youtube" and meta.get("transcript_status") in {
        "blocked",
        "disabled",
        "missing",
        "empty",
    }:
        source.normalized_text = None
    else:
        raise ValueError("No readable text extracted from this link")
    return source


def apply_pasted_transcript(source: Source, text: str) -> Source:
    if source.source_type != "youtube":
        raise ValueError("Transcript paste is only supported for YouTube sources.")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Transcript text cannot be empty.")
    meta = json.loads(source.length_meta or "{}")
    meta.update(
        {
            "words": len(cleaned.split()),
            "transcript_status": "pasted",
            "engine": "manual",
        }
    )
    source.normalized_text = cleaned
    source.length_meta = json.dumps(meta)
    return source


def update_source_record(conn: Any, source: Source) -> None:
    conn.execute(
        """
        UPDATE sources
        SET url = ?, title = ?, author = ?, length_meta = ?,
            normalized_text = ?, status = 'scoring'
        WHERE id = ?
        """,
        (
            source.url,
            source.title,
            source.author,
            source.length_meta,
            source.normalized_text,
            source.id,
        ),
    )
    conn.commit()


def mark_for_rescore(conn: Any, source_id: int) -> None:
    conn.execute("DELETE FROM scores WHERE source_id = ?", (source_id,))
    conn.execute("UPDATE sources SET status = 'scoring' WHERE id = ?", (source_id,))
    conn.commit()

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlite_vec import serialize_float32

from meridian.config import Settings
from meridian.ingest.platform import platform_for_source
from meridian.kb import embed
from meridian.kb.searchable import build_searchable_text
from meridian.store import db
from meridian.store import vault


WHAT_I_TOOK = re.compile(r"## What I took\s*\n(.*?)(?:\n## |\Z)", re.DOTALL)


def chunk_note(text: str) -> list[str]:
    match = WHAT_I_TOOK.search(text)
    if not match:
        return []
    body = match.group(1).strip()
    if not body:
        return []
    return [body]


def chunk_source_text(text: str, *, max_chars: int = 800) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    paragraphs = [part.strip() for part in stripped.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks if chunks else [stripped[:max_chars]]


def clear_source_embeddings(conn: Any, source_id: int) -> None:
    rows = conn.execute(
        "SELECT rowid FROM emb_meta WHERE source_id = ?", (source_id,)
    ).fetchall()
    for row in rows:
        conn.execute("DELETE FROM emb WHERE rowid = ?", (row["rowid"],))
    conn.execute("DELETE FROM emb_meta WHERE source_id = ?", (source_id,))


def index_source(conn: Any, source_id: int, *, settings: Settings) -> int:
    row = conn.execute(
        """
        SELECT s.title, s.url, s.genre, s.source_type, s.normalized_text,
               sc.framing, sc.theme_breakdown
        FROM sources s
        LEFT JOIN scores sc ON sc.source_id = s.id
        WHERE s.id = ?
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        return 0

    platform = platform_for_source(url=row["url"], source_type=row["source_type"])
    corpus = build_searchable_text(
        title=row["title"],
        url=row["url"],
        genre=row["genre"],
        source_type=row["source_type"],
        platform=platform,
        normalized_text=row["normalized_text"],
        framing_json=row["framing"],
        theme_breakdown_json=row["theme_breakdown"],
    )
    chunks = chunk_source_text(corpus)
    if not chunks:
        return 0

    clear_source_embeddings(conn, source_id)
    vectors = embed.embed_texts(chunks, settings=settings)
    added = 0
    for chunk, vector in zip(chunks, vectors, strict=True):
        cur = conn.execute(
            "INSERT INTO emb(embedding) VALUES (?)",
            (serialize_float32(vector),),
        )
        rowid = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO emb_meta (rowid, note_path, source_id, chunk_text) VALUES (?, ?, ?, ?)",
            (rowid, None, source_id, chunk),
        )
        added += 1
    return added


def reindex(conn: Any, *, settings: Settings) -> int:
    conn.execute("DELETE FROM emb_meta")
    conn.execute("DELETE FROM emb")
    conn.commit()
    count = 0
    for path in vault.iter_extractions(settings=settings):
        count += add_note(conn, path, settings=settings)
        conn.commit()
    source_rows = conn.execute(
        """
        SELECT id FROM sources
        WHERE status IN ('queued', 'captured')
          AND normalized_text IS NOT NULL
          AND TRIM(normalized_text) != ''
        """
    ).fetchall()
    for row in source_rows:
        count += index_source(conn, int(row["id"]), settings=settings)
        conn.commit()
    return count


def add_note(conn: Any, path: Path | str, *, settings: Settings) -> int:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    chunks = chunk_note(text)
    if not chunks:
        return 0
    vectors = embed.embed_texts(chunks, settings=settings)
    added = 0
    for chunk, vector in zip(chunks, vectors, strict=True):
        cur = conn.execute(
            "INSERT INTO emb(embedding) VALUES (?)",
            (serialize_float32(vector),),
        )
        rowid = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO emb_meta (rowid, note_path, source_id, chunk_text) VALUES (?, ?, ?, ?)",
            (rowid, str(path), None, chunk),
        )
        added += 1
    return added

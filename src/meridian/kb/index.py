from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlite_vec import serialize_float32

from meridian.config import Settings
from meridian.kb import embed
from meridian.store import db


WHAT_I_TOOK = re.compile(r"## What I took\s*\n(.*?)(?:\n## |\Z)", re.DOTALL)


def chunk_note(text: str) -> list[str]:
    match = WHAT_I_TOOK.search(text)
    if not match:
        return []
    body = match.group(1).strip()
    if not body:
        return []
    return [body]


def reindex(conn: Any, *, settings: Settings) -> int:
    conn.execute("DELETE FROM emb_meta")
    conn.execute("DELETE FROM emb")
    count = 0
    for path in sorted(settings.vault_path.glob("extraction-*.md")):
        count += add_note(conn, path, settings=settings)
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

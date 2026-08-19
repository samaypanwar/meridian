from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlite_vec import serialize_float32

from meridian.config import Settings
from meridian.kb import embed, query
from meridian.kb.query import Answer


@dataclass
class UnifiedSearchResult:
    query: str
    queue_source_ids: list[int]
    captures: Answer


def queue_source_ids(
    conn: Any,
    question: str,
    *,
    settings: Settings,
    limit: int = 10,
) -> list[int]:
    q_vec = embed.embed_texts([question], settings=settings)[0]
    rows = conn.execute(
        """
        SELECT m.source_id, e.distance
        FROM emb e
        JOIN emb_meta m ON m.rowid = e.rowid
        WHERE e.embedding MATCH ?
          AND k = ?
          AND m.source_id IS NOT NULL
        ORDER BY e.distance
        """,
        (serialize_float32(q_vec), max(limit * 5, 10)),
    ).fetchall()
    seen: set[int] = set()
    ordered: list[int] = []
    for row in rows:
        source_id = row["source_id"]
        if source_id is None or source_id in seen:
            continue
        seen.add(int(source_id))
        ordered.append(int(source_id))
        if len(ordered) >= limit:
            break
    return ordered


def unified(
    conn: Any,
    question: str,
    *,
    settings: Settings,
    limit: int = 10,
) -> UnifiedSearchResult:
    trimmed = question.strip()
    if not trimmed:
        return UnifiedSearchResult(
            query="",
            queue_source_ids=[],
            captures=Answer(text="", citations=[]),
        )
    captures = (
        query.believe(conn, trimmed, settings=settings)
        if settings.search_captures_enabled
        else Answer(text="", citations=[])
    )
    return UnifiedSearchResult(
        query=trimmed,
        queue_source_ids=queue_source_ids(
            conn, trimmed, settings=settings, limit=limit
        ),
        captures=captures,
    )

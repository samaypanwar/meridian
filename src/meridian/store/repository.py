from __future__ import annotations

import json
import sqlite3
from typing import Any

from meridian.ingest import canonical as canonical_mod
from meridian.store.models import Scores, Source, scores_from_row, source_from_row


def insert_source(conn: sqlite3.Connection, source: Source) -> Source:
    ref = source.url or source.blob_path or ""
    canonical_key = canonical_mod.canonical_ref(ref) if ref else None
    cur = conn.execute(
        """
        INSERT INTO sources (
          added_at, url, source_type, genre, title, author,
          length_meta, blob_path, normalized_text, status, canonical_ref
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source.added_at,
            source.url,
            source.source_type,
            source.genre,
            source.title,
            source.author,
            source.length_meta,
            source.blob_path,
            source.normalized_text,
            source.status,
            canonical_key,
        ),
    )
    source_id = int(cur.lastrowid)
    conn.commit()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    return source_from_row(row)


def insert_scores(conn: sqlite3.Connection, scores: Scores) -> Scores:
    conn.execute(
        """
        INSERT INTO scores (
          source_id, relevance, urgency0, effort, depth_required, curiosity,
          decay_lambda, theme_breakdown, rationale, confidence, scored_at,
          framing, reading_plan
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scores.source_id,
            scores.relevance,
            scores.urgency0,
            scores.effort,
            scores.depth_required,
            scores.curiosity,
            scores.decay_lambda,
            scores.theme_breakdown,
            scores.rationale,
            scores.confidence,
            scores.scored_at,
            scores.framing,
            scores.reading_plan,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM scores WHERE source_id = ?", (scores.source_id,)
    ).fetchone()
    return scores_from_row(row)


def get_source(conn: sqlite3.Connection, source_id: int) -> Source | None:
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if row is None:
        return None
    return source_from_row(row)


def find_by_canonical_ref(
    conn: sqlite3.Connection, canonical_key: str
) -> Source | None:
    row = conn.execute(
        """
        SELECT s.*
        FROM sources s
        LEFT JOIN scores sc ON sc.source_id = s.id
        WHERE s.canonical_ref = ?
        ORDER BY (sc.source_id IS NOT NULL) DESC, s.id ASC
        LIMIT 1
        """,
        (canonical_key,),
    ).fetchone()
    if row is not None:
        return source_from_row(row)

    legacy_matches: list[Any] = []
    for candidate in conn.execute(
        "SELECT * FROM sources WHERE canonical_ref IS NULL OR canonical_ref = ''"
    ):
        ref = candidate["url"] or candidate["blob_path"]
        if not ref:
            continue
        try:
            computed = canonical_mod.canonical_ref(ref)
        except ValueError:
            continue
        if computed == canonical_key:
            legacy_matches.append(candidate)

    if not legacy_matches:
        return None

    def _rank(candidate: Any) -> tuple[int, int]:
        has_scores = conn.execute(
            "SELECT 1 FROM scores WHERE source_id = ? LIMIT 1",
            (candidate["id"],),
        ).fetchone()
        return (1 if has_scores else 0, -int(candidate["id"]))

    best = max(legacy_matches, key=_rank)
    conn.execute(
        "UPDATE sources SET canonical_ref = ? WHERE id = ?",
        (canonical_key, best["id"]),
    )
    conn.commit()
    return source_from_row(best)


def get_scores(conn: sqlite3.Connection, source_id: int) -> Scores | None:
    row = conn.execute(
        "SELECT * FROM scores WHERE source_id = ?", (source_id,)
    ).fetchone()
    if row is None:
        return None
    return scores_from_row(row)


def source_with_scores(
    conn: sqlite3.Connection, source_id: int
) -> dict[str, Any] | None:
    source = get_source(conn, source_id)
    if source is None:
        return None
    scores = get_scores(conn, source_id)
    return {"source": source, "scores": scores}

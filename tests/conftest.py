from __future__ import annotations

import sqlite3
from pathlib import Path

from meridian.store import db


def insert_source_with_scores(
    conn: sqlite3.Connection,
    *,
    title: str,
    relevance: float,
    urgency0: float,
    effort: float,
    decay_lambda: float = 0.0,
    manual_rank: float | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO sources (added_at, url, source_type, genre, title, status)
        VALUES (datetime('now'), ?, 'web', 'nonfiction', ?, 'queued')
        """,
        (f"https://example.com/{title}", title),
    )
    source_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO scores (
          source_id, relevance, urgency0, effort, decay_lambda,
          theme_breakdown, confidence, scored_at
        ) VALUES (?, ?, ?, ?, ?, '{}', 'high', datetime('now'))
        """,
        (source_id, relevance, urgency0, effort, decay_lambda),
    )
    if manual_rank is not None:
        conn.execute(
            "INSERT INTO queue_overrides (source_id, manual_rank) VALUES (?, ?)",
            (source_id, manual_rank),
        )
    conn.commit()
    return source_id


def setup_db(path: Path) -> sqlite3.Connection:
    conn = db.connect(path)
    db.init_schema(conn)
    return conn

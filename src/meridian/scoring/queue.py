from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from meridian.scoring import priority
from meridian.store.models import Source, source_from_row


def _current_urgency(urgency0: float, decay_lambda: float, added_at: str) -> float:
    added = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
    if added.tzinfo is None:
        added = added.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    age_days = max((now - added).total_seconds() / 86400.0, 0.0)
    return priority.decay(urgency0, decay_lambda, age_days)


def _priority_for_row(row: sqlite3.Row) -> float:
    urgency = _current_urgency(row["urgency0"], row["decay_lambda"], row["added_at"])
    return priority.compute(row["relevance"], urgency, row["effort"])


def active(conn: sqlite3.Connection, limit: int = 10) -> list[Source]:
    rows = _queued_rows(conn)
    ranked = _rank_rows(rows)
    return [source_from_row(row) for row in ranked[:limit]]


def backlog(conn: sqlite3.Connection) -> list[Source]:
    rows = _queued_rows(conn)
    ranked = _rank_rows(rows)
    return [source_from_row(row) for row in ranked[10:]]


def _queued_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT s.*, sc.relevance, sc.urgency0, sc.effort, sc.decay_lambda,
               qo.manual_rank
        FROM sources s
        JOIN scores sc ON sc.source_id = s.id
        LEFT JOIN queue_overrides qo ON qo.source_id = s.id
        WHERE s.status = 'queued'
        """
    ).fetchall()
    return list(rows)


def _rank_rows(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    def sort_key(row: sqlite3.Row) -> tuple[float, float]:
        manual = row["manual_rank"]
        if manual is not None:
            return (manual, _priority_for_row(row))
        return (_priority_for_row(row), 0.0)

    return sorted(rows, key=sort_key, reverse=True)

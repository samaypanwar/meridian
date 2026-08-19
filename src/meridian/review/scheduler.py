from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from meridian.store.models import Review


def next_interval(interval: float, ease: float, grade: str) -> tuple[float, float]:
    if grade == "missed":
        return 1.0, max(1.3, ease - 0.2)
    if grade == "partial":
        new_interval = max(interval * 1.2, interval + 1.0)
        return new_interval, max(1.3, ease - 0.05)
    if grade == "got_it":
        if interval <= 1.0:
            new_interval = 3.0
        else:
            new_interval = interval * ease
        return new_interval, min(ease + 0.1, 3.0)
    raise ValueError(f"Unknown grade: {grade}")


def due(conn: Any, now: datetime | None = None) -> list[Review]:
    now = now or datetime.now(timezone.utc)
    now_iso = now.isoformat()
    rows = conn.execute(
        """
        SELECT * FROM reviews
        WHERE due_at <= ?
        ORDER BY due_at ASC
        """,
        (now_iso,),
    ).fetchall()
    return [
        Review(
            id=row["id"],
            note_path=row["note_path"],
            source_id=row["source_id"],
            question=row["question"],
            due_at=row["due_at"],
            interval_days=row["interval_days"],
            ease=row["ease"],
            history=row["history"],
        )
        for row in rows
    ]

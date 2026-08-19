from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Source:
    id: int | None
    added_at: str
    url: str | None
    source_type: str
    genre: str | None
    title: str | None
    author: str | None
    length_meta: str | None
    blob_path: str | None
    normalized_text: str | None
    status: str


@dataclass
class Scores:
    source_id: int
    relevance: float | None
    urgency0: float | None
    effort: float | None
    depth_required: float | None
    curiosity: float | None
    decay_lambda: float | None
    theme_breakdown: str | None
    rationale: str | None
    confidence: str | None
    scored_at: str | None
    framing: str | None = None
    reading_plan: str | None = None


@dataclass
class Review:
    id: int | None
    note_path: str
    source_id: int | None
    question: str
    due_at: str
    interval_days: float
    ease: float
    history: str | None


def source_from_row(row: Any) -> Source:
    return Source(
        id=row["id"],
        added_at=row["added_at"],
        url=row["url"],
        source_type=row["source_type"],
        genre=row["genre"],
        title=row["title"],
        author=row["author"],
        length_meta=row["length_meta"],
        blob_path=row["blob_path"],
        normalized_text=row["normalized_text"],
        status=row["status"],
    )


def scores_from_row(row: Any) -> Scores:
    return Scores(
        source_id=row["source_id"],
        relevance=row["relevance"],
        urgency0=row["urgency0"],
        effort=row["effort"],
        depth_required=row["depth_required"],
        curiosity=row["curiosity"],
        decay_lambda=row["decay_lambda"],
        theme_breakdown=row["theme_breakdown"],
        rationale=row["rationale"],
        confidence=row["confidence"],
        scored_at=row["scored_at"],
        framing=row["framing"] if "framing" in row.keys() else None,
        reading_plan=row["reading_plan"] if "reading_plan" in row.keys() else None,
    )

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AddSourceRequest(BaseModel):
    ref: str
    transcript: str | None = None


class TranscriptRequest(BaseModel):
    text: str


class CaptureRequest(BaseModel):
    reflection: str = ""


class CaptureApproveRequest(BaseModel):
    preview: str


class GradeRequest(BaseModel):
    grade: str


class SourceResponse(BaseModel):
    id: int
    title: str | None
    url: str | None
    source_type: str
    genre: str | None
    status: str
    normalized_text: str | None = None


class ScoresResponse(BaseModel):
    relevance: float | None
    urgency0: float | None
    effort: float | None
    depth_required: float | None
    curiosity: float | None
    theme_breakdown: dict[str, float] | None = None
    confidence: str | None
    framing: dict[str, Any] | None = None
    reading_plan: list[Any] | None = None


class AddSourceResponse(BaseModel):
    source: SourceResponse
    scores: ScoresResponse | None = None
    scoring_model: str
    status_message: str


class SourceDetailResponse(BaseModel):
    source: SourceResponse
    scores: ScoresResponse | None = None
    note_path: str | None = None


class QueueResponse(BaseModel):
    active: list[SourceDetailResponse]
    pending: list[SourceDetailResponse] = []
    backlog: list[SourceDetailResponse] = []

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from meridian.llm import client, prompts
from meridian.store.models import Scores, Source

DECAY_LAMBDA = {
    "timely": 0.1,
    "seasonal": 0.05,
    "evergreen": 0.0,
}


def score(source: Source, goals_md: str, *, model: str | None = None) -> Scores:
    template = prompts.load("ingest")
    user_block = _build_user_prompt(template, source, goals_md)
    messages = [
        {"role": "system", "content": _system_prompt(template)},
        {"role": "user", "content": user_block},
    ]
    payload = client.chat(messages, json_mode=True)
    return _parse_scores(source, payload)


def _system_prompt(template: str) -> str:
    if "## System" in template:
        return template.split("## System", 1)[1].split("## User", 1)[0].strip()
    return template


def _build_user_prompt(template: str, source: Source, goals_md: str) -> str:
    text_or_meta = source.normalized_text or json.dumps(
        {
            "title": source.title,
            "author": source.author,
            "length_meta": source.length_meta,
        }
    )
    filled = (
        template.replace("{{goals_md}}", goals_md)
        .replace("{{source_type}}", source.source_type)
        .replace("{{genre}}", source.genre or "")
        .replace("{{title}}", source.title or "")
        .replace("{{author}}", source.author or "")
        .replace("{{length_meta}}", source.length_meta or "")
        .replace("{{source_text_or_metadata}}", text_or_meta)
    )
    if "## User" in filled:
        return filled.split("## User", 1)[1].strip()
    return filled


def _parse_scores(source: Source, payload: dict[str, Any]) -> Scores:
    required = {
        "relevance",
        "curiosity",
        "depth_required",
        "effort_hours",
        "urgency",
        "theme_breakdown",
        "confidence",
    }
    if not required.issubset(payload.keys()):
        raise ValueError("Malformed ingest scoring response")

    urgency = payload["urgency"]
    decay_type = urgency.get("decay_type", "evergreen")
    decay_lambda = DECAY_LAMBDA.get(decay_type, 0.0)

    return Scores(
        source_id=source.id or 0,
        relevance=float(payload["relevance"]),
        urgency0=float(urgency["score"]),
        effort=float(payload["effort_hours"]),
        depth_required=float(payload["depth_required"]),
        curiosity=float(payload["curiosity"]),
        decay_lambda=decay_lambda,
        theme_breakdown=json.dumps(payload["theme_breakdown"]),
        rationale=json.dumps(payload.get("framing", {})),
        confidence=str(payload["confidence"]),
        scored_at=datetime.now(timezone.utc).isoformat(),
        framing=json.dumps(payload.get("framing", {})),
        reading_plan=json.dumps(payload.get("reading_plan", [])),
    )

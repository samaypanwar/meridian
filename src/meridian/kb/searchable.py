"""Build the searchable text corpus for queue sources (mirrors frontend queueFilters)."""

from __future__ import annotations

import json
from typing import Any

FRAMING_KEYS = (
    "display_title",
    "point",
    "matters_for_goals",
    "where_to_focus",
    "why_now",
    "skip_if",
)


def build_searchable_text(
    *,
    title: str | None,
    url: str | None,
    genre: str | None,
    source_type: str,
    platform: str,
    normalized_text: str | None,
    framing_json: str | None,
    theme_breakdown_json: str | None,
) -> str:
    parts: list[str] = []
    if title:
        parts.append(title)
    if url:
        parts.append(url)
    if genre:
        parts.append(genre)
    parts.append(source_type)
    parts.append(platform)

    if framing_json:
        framing = json.loads(framing_json)
        if isinstance(framing, dict):
            for key in FRAMING_KEYS:
                value = framing.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value)

    if theme_breakdown_json:
        themes = json.loads(theme_breakdown_json)
        if isinstance(themes, dict):
            for theme, score in themes.items():
                if isinstance(score, (int, float)) and score > 0:
                    parts.append(str(theme).replace("/", " "))

    if normalized_text:
        parts.append(normalized_text)

    return "\n".join(parts).lower()

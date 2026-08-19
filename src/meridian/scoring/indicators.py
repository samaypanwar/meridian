from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from meridian.config import Settings


def for_cycle(conn: Any, vault: Path, *, cycle: str | None = None) -> dict[str, Any]:
    captures_by_theme = _captures_by_theme(vault)
    pass_rate = _review_pass_rate(conn)
    hours_by_theme = _hours_placeholder()
    return {
        "captures_by_theme": captures_by_theme,
        "review_pass_rate": pass_rate,
        "hours_by_theme": hours_by_theme,
        "captures_this_cycle": sum(captures_by_theme.values()),
    }


def _captures_by_theme(vault: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not vault.exists():
        return counts
    for path in vault.glob("extraction-*.md"):
        text = path.read_text(encoding="utf-8")
        theme = _frontmatter_list_field(text, "goals")
        if not theme:
            theme = [_frontmatter_field(text, "topic") or "unknown"]
        for t in theme:
            counts[t] = counts.get(t, 0) + 1
    return counts


def _review_pass_rate(conn: Any) -> float:
    rows = conn.execute("SELECT history FROM reviews").fetchall()
    got_it = 0
    total = 0
    for row in rows:
        history = json.loads(row["history"] or "[]")
        for entry in history:
            total += 1
            if entry.get("grade") == "got_it":
                got_it += 1
    if total == 0:
        return 0.0
    return round(got_it / total, 2)


def _hours_placeholder() -> dict[str, float]:
    return {}


def _frontmatter_field(text: str, key: str) -> str | None:
    if not text.startswith("---"):
        return None
    front = text.split("---", 2)[1]
    for line in front.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def _frontmatter_list_field(text: str, key: str) -> list[str]:
    value = _frontmatter_field(text, key)
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        return [part.strip() for part in inner.split(",") if part.strip()]
    return [value]

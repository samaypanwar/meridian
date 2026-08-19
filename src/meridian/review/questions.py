from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from meridian.llm import client, prompts


def generate(capture_path: Path | str) -> dict[str, str]:
    text = Path(capture_path).read_text(encoding="utf-8")
    objective = _frontmatter_field(text, "objective") or ""
    what_i_took = _section(text, "What I took")
    template = prompts.load("review")
    filled = template.replace("{{objective}}", objective).replace(
        "{{what_i_took}}", what_i_took
    )
    messages = [
        {"role": "system", "content": _prompt_section(template, "System")},
        {"role": "user", "content": _prompt_section(filled, "User")},
    ]
    payload = client.chat(messages, json_mode=True)
    if "question" not in payload:
        raise ValueError("Malformed review question response")
    return {
        "question": str(payload["question"]),
        "ideal_answer_hint": str(payload.get("ideal_answer_hint", "")),
    }


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"## {re.escape(heading)}\s*\n(.*?)(?:\n## |\Z)", re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _frontmatter_field(text: str, key: str) -> str | None:
    if not text.startswith("---"):
        return None
    front = text.split("---", 2)[1]
    for line in front.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def _prompt_section(template: str, name: str) -> str:
    if f"## {name}" not in template:
        return template
    part = template.split(f"## {name}", 1)[1]
    for marker in ("## System", "## User"):
        if marker in part and marker != f"## {name}":
            part = part.split(marker, 1)[0]
    return part.strip()

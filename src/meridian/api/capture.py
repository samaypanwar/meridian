from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from meridian.config import Settings
from meridian.llm import client, prompts
from meridian.store import repository as repo
from meridian.store import vault


def draft_capture(
    source_id: int,
    reflection: str,
    *,
    conn: Any,
    settings: Settings,
    goals_md: str,
) -> dict[str, Any]:
    if not reflection.strip():
        return {"preview": "SHALLOW", "shallow": True}

    source = repo.get_source(conn, source_id)
    if source is None:
        raise ValueError("Source not found")
    scores = repo.get_scores(conn, source_id)

    template = prompts.load("capture")
    objective = ""
    if scores and scores.framing:
        framing = json.loads(scores.framing)
        objective = framing.get("matters_for_goals", "")

    filled = (
        template.replace("{{objective}}", objective)
        .replace("{{source_ref}}", source.url or source.title or "")
        .replace("{{source_type}}", source.source_type)
        .replace("{{goal_themes}}", ", ".join(_themes_from_goals(goals_md)))
        .replace("{{related_note_titles}}", "")
        .replace("{{user_reflection}}", reflection)
        .replace("{{today}}", datetime.now(timezone.utc).date().isoformat())
        .replace("{{best_topic_slug}}", "capture")
    )
    messages = [
        {"role": "system", "content": _section(template, "System")},
        {"role": "user", "content": _section(filled, "User") if "## User" in filled else filled},
    ]
    note = client.chat(messages)
    if isinstance(note, dict):
        note = note.get("note", json.dumps(note))
    if str(note).strip() == "SHALLOW":
        return {"preview": "SHALLOW", "shallow": True}
    return {"preview": str(note).strip(), "shallow": False}


def approve_capture(
    source_id: int,
    preview: str,
    *,
    conn: Any,
    settings: Settings,
) -> dict[str, str]:
    if preview.strip() == "SHALLOW":
        conn.execute("UPDATE sources SET status = 'revisit' WHERE id = ?", (source_id,))
        conn.commit()
        return {"note_path": "", "status": "revisit"}

    path = vault.write_extraction(preview, slug=f"source-{source_id}", settings=settings)
    conn.execute("UPDATE sources SET status = 'captured' WHERE id = ?", (source_id,))
    conn.commit()

    due_at = datetime.now(timezone.utc) + timedelta(days=1)
    conn.execute(
        """
        INSERT INTO reviews (note_path, source_id, question, due_at, interval_days, ease, history)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(path),
            source_id,
            "Pending question generation",
            due_at.isoformat(),
            1.0,
            2.5,
            "[]",
        ),
    )
    conn.commit()
    return {"note_path": str(path), "status": "captured"}


def _section(template: str, name: str) -> str:
    if f"## {name}" not in template:
        return template
    part = template.split(f"## {name}", 1)[1]
    for marker in ("## System", "## User"):
        if marker in part and marker != f"## {name}":
            part = part.split(marker, 1)[0]
    return part.strip()


def _themes_from_goals(goals_md: str) -> list[str]:
    themes: list[str] = []
    in_themes = False
    for line in goals_md.splitlines():
        if line.strip().startswith("## Themes"):
            in_themes = True
            continue
        if in_themes and line.startswith("## "):
            break
        if in_themes and line.strip().startswith("- "):
            themes.append(line.strip()[2:])
    return themes

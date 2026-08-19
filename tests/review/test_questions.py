import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.store import db


def test_grade_missed_twice_flags_revisit(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", vault_path=tmp_path / "vault")
    conn = db.connect(settings.db_path)
    db.init_schema(conn)
    conn.execute(
        "INSERT INTO sources (added_at, source_type, status) VALUES (?, 'web', 'captured')",
        (datetime.now(timezone.utc).isoformat(),),
    )
    source_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    due = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conn.execute(
        """
        INSERT INTO reviews (note_path, source_id, question, due_at, interval_days, ease, history)
        VALUES ('note.md', ?, 'Q?', ?, 1.0, 2.5, '[]')
        """,
        (source_id, due),
    )
    conn.commit()
    review_id = conn.execute("SELECT id FROM reviews").fetchone()[0]
    conn.close()

    app = create_app(settings)
    with TestClient(app) as client:
        with patch("meridian.review.questions.client.chat", return_value={"question": "Q?", "ideal_answer_hint": ""}):
            first = client.post(f"/reviews/{review_id}/grade", json={"grade": "missed"})
            assert first.status_code == 200, first.text
            resp = client.post(f"/reviews/{review_id}/grade", json={"grade": "missed"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "revisit"


def test_questions_generate_from_fixture(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text(
        """---
objective: Test objective
---

# Title

## What I took
The baseline reduces variance in policy gradients.
"""
    )
    with patch(
        "meridian.review.questions.client.chat",
        return_value={"question": "Why use a baseline?", "ideal_answer_hint": "variance"},
    ):
        from meridian.review import questions

        result = questions.generate(note)
    assert "baseline" in result["question"].lower()

from pathlib import Path
from unittest.mock import patch

from meridian.config import Settings
from meridian.kb import index, query
from meridian.store import db


def test_believe_returns_relevant_capture(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        embed_model="stub",
    )
    settings.capture_path.mkdir(parents=True)
    (settings.capture_path / "extraction-2026-08-19-rl.md").write_text(
        """---
type: extraction
---

# RL note

## What I took
Policy gradient increases reward in the direction of the gradient.
"""
    )
    (settings.capture_path / "extraction-2026-08-19-la.md").write_text(
        """---
type: extraction
---

# LA note

## What I took
Eigenvectors diagonalize linear transformations.
"""
    )
    conn = db.connect(settings.db_path)
    db.init_schema(conn)
    index.reindex(conn, settings=settings)

    with patch("meridian.kb.query.client.chat", side_effect=Exception("offline")):
        answer = query.believe(conn, "policy gradient reward", settings=settings)
    assert answer.citations
    assert "policy gradient" in answer.text.lower() or "gradient" in answer.text.lower()

import json
from unittest.mock import patch

from meridian.api.scoring_worker import score_source_in_background
from meridian.config import Settings
from meridian.scoring.radar import _parse_scores
from meridian.store import db
from meridian.store.models import Source


def test_scoring_worker_updates_title_from_display_title(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault",
        openrouter_api_key="test",
        embed_model="stub",
    )
    conn = db.connect(settings.db_path)
    db.init_schema(conn)
    source = Source(
        id=None,
        added_at="2026-08-19T00:00:00+00:00",
        url="https://github.com/openai/spinningup",
        source_type="web",
        genre="nonfiction",
        title="GitHub - openai/spinningup: Educational RL resource",
        author=None,
        length_meta='{"words": 100}',
        blob_path=None,
        normalized_text="Educational RL content.",
        status="scoring",
    )
    from meridian.store import repository as repo

    saved = repo.insert_source(conn, source)
    conn.close()

    payload = {
        "relevance": 8,
        "curiosity": 6,
        "depth_required": 7,
        "effort_hours": 2,
        "urgency": {"score": 5, "decay_type": "evergreen"},
        "theme_breakdown": {"foundations/rl": 8},
        "confidence": "high",
        "framing": {
            "display_title": "Spinning Up in Deep RL",
            "point": "Educational RL walkthrough",
            "matters_for_goals": "Matches RL objective",
            "where_to_focus": "Policy gradient sections",
            "why_now": "Supports current cycle objective",
            "skip_if": "You already completed the exercises",
        },
        "reading_plan": [],
    }

    with patch("meridian.api.scoring_worker.radar.score") as mock_score:
        mock_score.side_effect = lambda source, goals_md, **_: _parse_scores(
            source, payload
        )
        score_source_in_background(saved.id or 0, settings)

    conn = db.connect(settings.db_path)
    row = conn.execute(
        "SELECT title, status FROM sources WHERE id = ?", (saved.id,)
    ).fetchone()
    conn.close()
    assert row["title"] == "Spinning Up in Deep RL"
    assert row["status"] == "queued"

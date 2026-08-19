from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.store import db


def _radar_payload() -> dict:
    return {
        "relevance": 8,
        "curiosity": 6,
        "depth_required": 7,
        "effort_hours": 2,
        "urgency": {"score": 5, "decay_type": "evergreen"},
        "theme_breakdown": {"foundations/rl": 8},
        "confidence": "high",
        "framing": {"point": "x", "matters_for_goals": "y", "where_to_focus": "z"},
        "reading_plan": [],
    }


def test_refetch_updates_title_and_rescores(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault",
        openrouter_api_key="test",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        with patch(
            "meridian.api.app.fetch_normalized",
            return_value=("old body", {"title": "Old"}, "https://x.com"),
        ):
            with patch("meridian.api.scoring_worker.radar.score") as mock_score:
                from meridian.scoring.radar import _parse_scores

                mock_score.side_effect = lambda source, goals_md, **_: _parse_scores(
                    source, _radar_payload()
                )
                created = client.post("/sources", json={"ref": "https://x.com"})
        source_id = created.json()["source"]["id"]

        with patch(
            "meridian.api.source_ops.fetch_normalized",
            return_value=(
                "Full article body about policy gradients.",
                {"title": "Real Title", "author": "Author"},
                "https://x.com",
            ),
        ):
            with patch("meridian.api.scoring_worker.radar.score") as mock_score:
                from meridian.scoring.radar import _parse_scores

                mock_score.side_effect = lambda source, goals_md, **_: _parse_scores(
                    source, _radar_payload()
                )
                resp = client.post(f"/sources/{source_id}/refetch")

        assert resp.status_code == 202
        detail = client.get(f"/sources/{source_id}").json()
        assert detail["source"]["title"] == "Real Title"
        assert "policy gradients" in detail["source"]["normalized_text"]
        assert detail["scores"]["relevance"] == 8


def test_rescore_without_text_returns_422(tmp_path) -> None:
    settings = Settings(data_dir=tmp_path / "data", vault_path=tmp_path / "vault")
    app = create_app(settings)
    conn = db.connect(settings.db_path)
    db.init_schema(conn)
    conn.execute(
        "INSERT INTO sources (added_at, url, source_type, genre, title, status) "
        "VALUES ('2026-08-19', 'https://example.com', 'web', 'nonfiction', 'Example', 'queued')"
    )
    source_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    with TestClient(app) as client:
        resp = client.post(f"/sources/{source_id}/rescore")
    assert resp.status_code == 422

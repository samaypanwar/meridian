import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings


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


def test_post_sources_and_get_queue(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        openrouter_api_key="test",
        embed_model="stub",
    )
    with patch(
        "meridian.api.app.fetch_normalized",
        return_value=(
            "Article text",
            {"title": "Example", "words": 100},
            "https://example.com/article",
        ),
    ):
        with patch("meridian.api.scoring_worker.radar.score") as mock_score:
            from meridian.scoring.radar import _parse_scores
            from meridian.store.models import Source

            def fake_score(source: Source, goals_md: str, **_: object):
                return _parse_scores(source, _radar_payload())

            mock_score.side_effect = fake_score
            app = create_app(settings)
            with TestClient(app) as client:
                resp = client.post(
                    "/sources", json={"ref": "https://example.com/article"}
                )
                assert resp.status_code == 202
                data = resp.json()
                assert data["source"]["source_type"] == "web"
                assert data["scores"] is None
                assert "scoring_model" in data

                detail = client.get(f"/sources/{data['source']['id']}")
                assert detail.status_code == 200
                assert detail.json()["scores"]["relevance"] == 8
                assert detail.json()["source"]["status"] == "queued"

                queue_resp = client.get("/queue")
                assert queue_resp.status_code == 200
                assert len(queue_resp.json()["active"]) == 1

                assert detail.json()["source"]["id"] == data["source"]["id"]

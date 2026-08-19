import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings


def test_post_sources_and_get_queue(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        openrouter_api_key="test",
    )
    radar_payload = {
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
    with patch("meridian.api.app.web.fetch_text", return_value=("Article text", {"words": 100})):
        with patch("meridian.scoring.radar.client.chat", return_value=radar_payload):
            app = create_app(settings)
            with TestClient(app) as client:
                resp = client.post("/sources", json={"ref": "https://example.com/article"})
                assert resp.status_code == 200
                data = resp.json()
                assert data["source"]["source_type"] == "web"
                assert data["scores"]["relevance"] == 8

                queue_resp = client.get("/queue")
                assert queue_resp.status_code == 200
                assert len(queue_resp.json()["active"]) == 1

                detail = client.get(f"/sources/{data['source']['id']}")
                assert detail.status_code == 200
                assert detail.json()["source"]["id"] == data["source"]["id"]

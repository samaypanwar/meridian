from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings


def test_capture_preview_and_shallow(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        openrouter_api_key="test",
        embed_model="stub",
    )
    note = """---
type: extraction
goals: [foundations/rl]
---

# Capture

## What I took
Policy gradient estimates direction of improvement.
"""
    app = create_app(settings)
    with TestClient(app) as client:
        with patch(
            "meridian.api.app.fetch_normalized",
            return_value=(
                "text",
                {"title": "Article", "words": 10},
                "https://example.com",
            ),
        ):
            with patch("meridian.api.scoring_worker.radar.score") as mock_score:
                from meridian.scoring.radar import _parse_scores
                from meridian.store.models import Source

                def fake_score(source: Source, goals_md: str, **_: object):
                    return _parse_scores(source, _radar_payload())

                mock_score.side_effect = fake_score
                created = client.post("/sources", json={"ref": "https://example.com/x"})
        source_id = created.json()["source"]["id"]

        shallow = client.post(
            f"/sources/{source_id}/capture",
            json={"reflection": "   "},
        )
        assert shallow.status_code == 200, shallow.text
        assert shallow.json()["shallow"] is True

        with patch(
            "meridian.api.capture.client.chat",
            return_value=note,
        ):
            preview = client.post(
                f"/sources/{source_id}/capture",
                json={"reflection": "I took the policy gradient direction idea."},
            )
        assert "What I took" in preview.json()["preview"]

        with patch(
            "meridian.review.questions.client.chat",
            return_value={"question": "Q?", "ideal_answer_hint": "A"},
        ):
            approved = client.post(
                f"/sources/{source_id}/capture/approve",
                json={"preview": preview.json()["preview"]},
            )
        assert approved.json()["status"] == "captured"
        assert approved.json()["note_path"]


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

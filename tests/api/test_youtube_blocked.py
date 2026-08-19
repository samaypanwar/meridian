from unittest.mock import patch

from fastapi.testclient import TestClient
from youtube_transcript_api._errors import IpBlocked

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.scoring.radar import _parse_scores


def _radar_payload() -> dict:
    return {
        "relevance": 4,
        "curiosity": 6,
        "depth_required": 5,
        "effort_hours": 1,
        "urgency": {"score": 3, "decay_type": "evergreen"},
        "theme_breakdown": {"foundations/rl": 4},
        "confidence": "low",
        "framing": {
            "display_title": "Example RL Talk",
            "point": "Metadata-only score",
            "matters_for_goals": "Uncertain without transcript",
            "where_to_focus": "Watch the video",
            "why_now": "Maybe later",
            "skip_if": "If blocked persists",
        },
        "reading_plan": [],
    }


def test_youtube_ip_block_still_ingests_for_metadata_scoring(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault",
        openrouter_api_key="test",
    )
    app = create_app(settings)
    url = "https://www.youtube.com/watch?v=F25i0sgrp9M"

    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "Example RL Talk", "author": "Channel"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            side_effect=IpBlocked(url),
        ):
            with patch("meridian.api.scoring_worker.radar.score") as mock_score:
                mock_score.side_effect = lambda source, goals_md, **_: _parse_scores(
                    source, _radar_payload()
                )
                with TestClient(app) as client:
                    resp = client.post("/sources", json={"ref": url})

    assert resp.status_code == 202
    data = resp.json()
    assert data["source"]["source_type"] == "youtube"
    assert data["source"]["title"] == "Example RL Talk"
    assert "blocked" in data["status_message"].lower()
    assert data["source"]["normalized_text"] is None


def test_paste_transcript_rescores_youtube_source(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault",
        openrouter_api_key="test",
    )
    app = create_app(settings)
    url = "https://www.youtube.com/watch?v=F25i0sgrp9M"

    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "Example RL Talk", "author": "Channel"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            side_effect=IpBlocked(url),
        ):
            with patch("meridian.api.scoring_worker.radar.score") as mock_score:
                mock_score.side_effect = lambda source, goals_md, **_: _parse_scores(
                    source, _radar_payload()
                )
                with TestClient(app) as client:
                    created = client.post("/sources", json={"ref": url})
                    source_id = created.json()["source"]["id"]
                    resp = client.post(
                        f"/sources/{source_id}/transcript",
                        json={
                            "text": "Policy gradients estimate the direction of improvement."
                        },
                    )
                    assert resp.status_code == 202
                    detail = client.get(f"/sources/{source_id}").json()
                    assert (
                        "policy gradients"
                        in detail["source"]["normalized_text"].lower()
                    )

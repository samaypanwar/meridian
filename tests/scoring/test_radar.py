import json
from unittest.mock import patch

import pytest

from meridian.scoring import radar
from meridian.store.models import Source


def _sample_source() -> Source:
    return Source(
        id=1,
        added_at="2026-08-19T00:00:00+00:00",
        url="https://example.com",
        source_type="web",
        genre="nonfiction",
        title="Test Article",
        author=None,
        length_meta='{"words": 1000}',
        blob_path=None,
        normalized_text="Sample text about policy gradients.",
        status="queued",
    )


def test_radar_score_parses_mocked_response() -> None:
    payload = {
        "relevance": 8,
        "curiosity": 6,
        "depth_required": 7,
        "effort_hours": 2,
        "urgency": {"score": 5, "decay_type": "timely"},
        "theme_breakdown": {"foundations/rl": 8},
        "confidence": "high",
        "framing": {
            "point": "Explains policy gradients",
            "matters_for_goals": "Matches RL objective",
            "where_to_focus": "Theorem section",
        },
        "reading_plan": [],
    }
    with patch("meridian.scoring.radar.client.chat", return_value=payload):
        scores = radar.score(_sample_source(), goals_md="# goals")
    assert scores.relevance == 8
    assert scores.curiosity == 6
    assert scores.depth_required == 7
    assert scores.effort == 2
    assert scores.urgency0 == 5
    assert scores.decay_lambda == 0.1
    assert json.loads(scores.theme_breakdown or "{}") == {"foundations/rl": 8}
    assert scores.confidence == "high"


def test_radar_score_rejects_malformed_json() -> None:
    with patch("meridian.scoring.radar.client.chat", return_value={"bad": "data"}):
        with pytest.raises(ValueError):
            radar.score(_sample_source(), goals_md="# goals")

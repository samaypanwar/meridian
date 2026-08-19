import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.scoring.radar import _parse_scores
from tests.conftest import insert_source_with_scores, setup_db


def _radar_payload() -> dict:
    return {
        "relevance": 8,
        "curiosity": 6,
        "depth_required": 7,
        "effort_hours": 2,
        "urgency": {"score": 5, "decay_type": "evergreen"},
        "theme_breakdown": {"foundations/rl": 8},
        "confidence": "high",
        "framing": {
            "display_title": "RL Foundations",
            "point": "Policy gradient methods",
            "matters_for_goals": "Supports foundations/rl",
            "where_to_focus": "Intro section",
            "why_now": "This cycle",
            "skip_if": "Already expert",
        },
        "reading_plan": [],
    }


def test_search_returns_queue_matches_without_captures_by_default(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        openrouter_api_key="test",
        embed_model="stub",
    )
    settings.capture_path.mkdir(parents=True)
    (settings.capture_path / "extraction-2026-08-19-alpha.md").write_text(
        """---
type: extraction
---

# Note

## What I took
Belief about policy gradient variance.
"""
    )
    conn = setup_db(settings.db_path)
    source_id = insert_source_with_scores(
        conn,
        title="RL Talk",
        relevance=8.0,
        urgency0=5.0,
        effort=1.0,
    )
    conn.execute(
        "UPDATE scores SET framing = ? WHERE source_id = ?",
        (json.dumps(_radar_payload()["framing"]), source_id),
    )
    conn.execute(
        "UPDATE sources SET normalized_text = ? WHERE id = ?",
        ("Policy gradient variance reduction techniques.", source_id),
    )
    conn.commit()

    from meridian.kb import index as kb_index

    kb_index.reindex(conn, settings=settings)

    app = create_app(settings)
    with TestClient(app) as client:
        with patch("meridian.kb.query.client.chat") as mock_chat:
            resp = client.get("/search", params={"q": "policy gradient variance"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "policy gradient variance"
    assert len(data["queue"]) >= 1
    assert data["queue"][0]["source"]["title"] == "RL Talk"
    assert data["captures"]["text"] == ""
    assert data["captures"]["citations"] == []
    mock_chat.assert_not_called()


def test_search_includes_captures_when_enabled(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        openrouter_api_key="test",
        embed_model="stub",
        search_captures_enabled=True,
    )
    settings.capture_path.mkdir(parents=True)
    (settings.capture_path / "extraction-2026-08-19-alpha.md").write_text(
        """---
type: extraction
---

# Note

## What I took
Belief about policy gradient variance.
"""
    )
    conn = setup_db(settings.db_path)
    source_id = insert_source_with_scores(
        conn,
        title="RL Talk",
        relevance=8.0,
        urgency0=5.0,
        effort=1.0,
    )
    conn.execute(
        "UPDATE sources SET normalized_text = ? WHERE id = ?",
        ("Policy gradient variance reduction techniques.", source_id),
    )
    conn.commit()

    from meridian.kb import index as kb_index

    kb_index.reindex(conn, settings=settings)

    app = create_app(settings)
    with TestClient(app) as client:
        with patch(
            "meridian.kb.query.client.chat",
            return_value="You believe variance matters.",
        ):
            resp = client.get("/search", params={"q": "policy gradient variance"})

    assert resp.status_code == 200
    data = resp.json()
    assert "variance" in data["captures"]["text"].lower()


def test_queue_returns_full_ranked_list(tmp_path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        openrouter_api_key="test",
    )
    conn = setup_db(settings.db_path)
    for i in range(12):
        insert_source_with_scores(
            conn,
            title=f"item-{i}",
            relevance=float(i + 1),
            urgency0=5.0,
            effort=1.0,
        )
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/queue")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["queued"]) == 12
    assert len(data["active"]) == 10
    assert len(data["backlog"]) == 2

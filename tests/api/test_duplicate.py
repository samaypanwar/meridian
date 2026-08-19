from unittest.mock import patch

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.ingest.canonical import canonical_ref
from tests.conftest import insert_source_with_scores, setup_db


def test_duplicate_source_returns_409_without_fetch(tmp_path) -> None:
    url = "https://example.com/article"
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        openrouter_api_key="test",
        embed_model="stub",
    )
    conn = setup_db(settings.db_path)
    source_id = insert_source_with_scores(
        conn,
        title="Existing article",
        relevance=7.0,
        urgency0=4.0,
        effort=1.0,
    )
    conn.execute(
        "UPDATE sources SET url = ?, canonical_ref = ? WHERE id = ?",
        (url, canonical_ref(url), source_id),
    )
    conn.commit()
    conn.close()

    app = create_app(settings)
    with patch("meridian.api.app.fetch_normalized") as mock_fetch:
        with TestClient(app) as client:
            resp = client.post(
                "/sources",
                json={"ref": "https://example.com/article?utm_source=newsletter"},
            )

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["message"] == "This source is already in Meridian."
    assert detail["existing"]["source"]["id"] == source_id
    assert detail["existing"]["scores"]["relevance"] == 7.0
    mock_fetch.assert_not_called()


def test_duplicate_prefers_scored_source_over_orphan(tmp_path) -> None:
    url = "https://www.lesswrong.com/posts/uMQ3cqWDPHhjtiesc/example"
    canonical = canonical_ref(url)
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        openrouter_api_key="test",
        embed_model="stub",
    )
    conn = setup_db(settings.db_path)
    orphan_id = conn.execute(
        """
        INSERT INTO sources (added_at, url, source_type, status)
        VALUES (datetime('now'), ?, 'web', 'queued')
        """,
        (url,),
    ).lastrowid
    scored_id = insert_source_with_scores(
        conn,
        title="Scored duplicate",
        relevance=8.0,
        urgency0=5.0,
        effort=2.0,
    )
    conn.execute(
        "UPDATE sources SET url = ?, source_type = 'web', canonical_ref = ? WHERE id = ?",
        (url, canonical, scored_id),
    )
    conn.commit()
    conn.close()

    app = create_app(settings)
    with patch("meridian.api.app.fetch_normalized") as mock_fetch:
        with TestClient(app) as client:
            resp = client.post("/sources", json={"ref": url})

    assert resp.status_code == 409
    existing_id = resp.json()["detail"]["existing"]["source"]["id"]
    assert existing_id == scored_id
    assert existing_id != orphan_id
    mock_fetch.assert_not_called()

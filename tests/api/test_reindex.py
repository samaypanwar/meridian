from pathlib import Path

from fastapi.testclient import TestClient

from meridian.api.app import create_app
from meridian.config import Settings
from meridian.kb import index
from meridian.store import db
from tests.conftest import insert_source_with_scores, setup_db


def test_reindex_route_on_fresh_connection(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        embed_model="stub",
    )
    settings.capture_path.mkdir(parents=True)
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
        ("Policy gradients estimate improvement direction.", source_id),
    )
    conn.commit()
    conn.close()

    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.post("/reindex")

    assert resp.status_code == 200
    assert resp.json()["indexed_chunks"] >= 1


def test_connect_loads_vec_for_reindex(tmp_path: Path) -> None:
    path = tmp_path / "data" / "meridian.db"
    conn = db.connect(path)
    db.init_schema(conn)
    conn.execute("DELETE FROM emb_meta")
    conn.execute("DELETE FROM emb")
    conn.commit()
    conn.close()

    fresh = db.connect(path)
    fresh.execute("DELETE FROM emb")
    fresh.commit()
    fresh.close()

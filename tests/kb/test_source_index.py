from pathlib import Path

from meridian.config import Settings
from meridian.kb import index
from meridian.store import db
from tests.conftest import insert_source_with_scores, setup_db


def test_index_source_creates_embeddings_for_queue_item(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        embed_model="stub",
    )
    conn = setup_db(tmp_path / "test.db")
    source_id = insert_source_with_scores(
        conn,
        title="RL Talk",
        relevance=8.0,
        urgency0=5.0,
        effort=1.0,
    )
    conn.execute(
        """
        UPDATE scores SET framing = ?
        WHERE source_id = ?
        """,
        ('{"point": "Policy gradients overview"}', source_id),
    )
    conn.execute(
        """
        UPDATE sources
        SET normalized_text = ?
        WHERE id = ?
        """,
        ("Policy gradients estimate the direction of improvement.", source_id),
    )
    conn.commit()

    added = index.index_source(conn, source_id, settings=settings)
    conn.commit()
    assert added >= 1
    rows = conn.execute(
        "SELECT source_id, chunk_text FROM emb_meta WHERE source_id = ?",
        (source_id,),
    ).fetchall()
    assert len(rows) >= 1
    assert "policy gradients" in rows[0]["chunk_text"].lower()


def test_reindex_includes_sources_and_captures(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        capture_path=tmp_path / "vault" / "learnings" / "meridian",
        embed_model="stub",
    )
    settings.capture_path.mkdir(parents=True)
    (settings.capture_path / "extraction-2026-08-19-alpha.md").write_text(
        """---
type: extraction
---

# Note

## What I took
Capture about Sutton and Barto.
"""
    )
    conn = setup_db(tmp_path / "test.db")
    source_id = insert_source_with_scores(
        conn,
        title="Textbook",
        relevance=5.0,
        urgency0=5.0,
        effort=1.0,
    )
    conn.execute(
        "UPDATE sources SET normalized_text = ? WHERE id = ?",
        ("Chapter on value functions.", source_id),
    )
    conn.commit()

    count = index.reindex(conn, settings=settings)
    assert count >= 2
    note_rows = conn.execute(
        "SELECT COUNT(*) AS c FROM emb_meta WHERE note_path IS NOT NULL"
    ).fetchone()
    source_rows = conn.execute(
        "SELECT COUNT(*) AS c FROM emb_meta WHERE source_id IS NOT NULL"
    ).fetchone()
    assert note_rows["c"] >= 1
    assert source_rows["c"] >= 1

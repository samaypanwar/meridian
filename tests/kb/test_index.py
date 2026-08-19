from pathlib import Path

from meridian.config import Settings
from meridian.kb import index
from meridian.store import db


def test_reindex_creates_emb_meta_rows(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        vault_path=tmp_path / "vault" / "00-inbox",
        embed_model="stub",
    )
    settings.vault_path.mkdir(parents=True)
    note = """---
type: extraction
---

# Note one

## What I took
First capture chunk about RL.

## Connections
"""
    (settings.vault_path / "extraction-2026-08-19-alpha.md").write_text(note)
    note2 = note.replace("First capture", "Second capture")
    (settings.vault_path / "extraction-2026-08-19-beta.md").write_text(note2)

    conn = db.connect(settings.db_path)
    db.init_schema(conn)
    count = index.reindex(conn, settings=settings)
    assert count == 2
    rows = conn.execute("SELECT note_path, chunk_text FROM emb_meta").fetchall()
    assert len(rows) == 2
    paths = {row["note_path"] for row in rows}
    assert len(paths) == 2

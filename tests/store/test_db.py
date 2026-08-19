import sqlite3
from pathlib import Path

from meridian.store import db


def test_init_schema_creates_tables(tmp_path: Path) -> None:
    conn = db.connect(tmp_path / "test.db")
    db.init_schema(conn)
    rows = conn.execute(
        "SELECT name, type FROM sqlite_master WHERE name IN "
        "('sources', 'scores', 'queue_overrides', 'reviews', 'emb_meta', 'emb')"
    ).fetchall()
    names = {name for name, _ in rows}
    assert names == {"sources", "scores", "queue_overrides", "reviews", "emb_meta", "emb"}
    conn.close()

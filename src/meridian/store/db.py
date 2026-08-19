from __future__ import annotations

from pathlib import Path

import pysqlite3 as sqlite3  # noqa: F401 — extension-capable SQLite
import sqlite_vec

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources (
  id              INTEGER PRIMARY KEY,
  added_at        TEXT NOT NULL,
  url             TEXT,
  source_type     TEXT NOT NULL,
  genre           TEXT,
  title           TEXT,
  author          TEXT,
  length_meta     TEXT,
  blob_path       TEXT,
  normalized_text TEXT,
  status          TEXT NOT NULL,
  canonical_ref   TEXT
);

CREATE TABLE IF NOT EXISTS scores (
  source_id       INTEGER PRIMARY KEY REFERENCES sources(id),
  relevance       REAL,
  urgency0        REAL,
  effort          REAL,
  depth_required  REAL,
  curiosity       REAL,
  decay_lambda    REAL,
  theme_breakdown TEXT,
  rationale       TEXT,
  confidence      TEXT,
  scored_at       TEXT,
  framing         TEXT,
  reading_plan    TEXT
);

CREATE TABLE IF NOT EXISTS queue_overrides (
  source_id       INTEGER PRIMARY KEY REFERENCES sources(id),
  manual_rank     REAL,
  note            TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
  id              INTEGER PRIMARY KEY,
  note_path       TEXT NOT NULL,
  source_id       INTEGER REFERENCES sources(id),
  question        TEXT NOT NULL,
  due_at          TEXT NOT NULL,
  interval_days   REAL NOT NULL,
  ease            REAL NOT NULL,
  history         TEXT
);

CREATE TABLE IF NOT EXISTS emb_meta (
  rowid           INTEGER PRIMARY KEY,
  note_path       TEXT,
  source_id       INTEGER,
  chunk_text      TEXT
);
"""

EMB_DIM = 384


def connect(path: Path | str) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    _load_vec_extension(conn)
    return conn


def _load_vec_extension(conn: sqlite3.Connection) -> None:
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS emb USING vec0(
          embedding float[{EMB_DIM}]
        )
        """
    )
    migrate_schema(conn)
    conn.commit()


def migrate_schema(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(sources)")}
    if "canonical_ref" not in columns:
        conn.execute("ALTER TABLE sources ADD COLUMN canonical_ref TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sources_canonical_ref ON sources(canonical_ref)"
    )
    _backfill_canonical_refs(conn)


def _backfill_canonical_refs(conn: sqlite3.Connection) -> None:
    from meridian.ingest import canonical

    rows = conn.execute(
        "SELECT id, url, blob_path FROM sources WHERE canonical_ref IS NULL"
    ).fetchall()
    for row in rows:
        ref = row["url"] or row["blob_path"]
        if not ref:
            continue
        try:
            key = canonical.canonical_ref(ref)
        except ValueError:
            continue
        conn.execute(
            "UPDATE sources SET canonical_ref = ? WHERE id = ?",
            (key, row["id"]),
        )

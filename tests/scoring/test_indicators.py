from pathlib import Path

from meridian.config import Settings
from meridian.scoring import indicators
from meridian.store import db


def test_indicators_capture_counts_and_pass_rate(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "extraction-2026-08-19-a.md").write_text(
        """---
type: extraction
goals: [foundations/rl]
---

# A

## What I took
One
"""
    )
    (vault / "extraction-2026-08-19-b.md").write_text(
        """---
type: extraction
goals: [foundations/rl, foundations/linear-algebra]
---

# B

## What I took
Two
"""
    )
    conn = db.connect(tmp_path / "test.db")
    db.init_schema(conn)
    conn.execute(
        """
        INSERT INTO reviews (note_path, question, due_at, interval_days, ease, history)
        VALUES ('a.md', 'Q', datetime('now'), 1.0, 2.5, ?)
        """,
        (
            '[{"date":"2026-08-19","grade":"got_it"},{"date":"2026-08-19","grade":"missed"}]',
        ),
    )
    conn.commit()

    result = indicators.for_cycle(conn, vault)
    assert result["captures_by_theme"]["foundations/rl"] == 2
    assert result["captures_by_theme"]["foundations/linear-algebra"] == 1
    assert result["review_pass_rate"] == 0.5

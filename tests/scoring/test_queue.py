from pathlib import Path

from meridian.scoring import queue
from tests.conftest import insert_source_with_scores, setup_db


def test_active_returns_top_ten_by_priority(tmp_path: Path) -> None:
    conn = setup_db(tmp_path / "test.db")
    for i in range(12):
        insert_source_with_scores(
            conn,
            title=f"item-{i}",
            relevance=float(i + 1),
            urgency0=5.0,
            effort=1.0,
        )
    active = queue.active(conn, limit=10)
    assert len(active) == 10
    titles = [s.title for s in active]
    assert "item-11" in titles
    assert "item-0" not in titles


def test_manual_rank_floats_item_up(tmp_path: Path) -> None:
    conn = setup_db(tmp_path / "test.db")
    insert_source_with_scores(
        conn, title="low", relevance=1.0, urgency0=5.0, effort=1.0
    )
    insert_source_with_scores(
        conn,
        title="boosted",
        relevance=1.0,
        urgency0=5.0,
        effort=1.0,
        manual_rank=999.0,
    )
    insert_source_with_scores(
        conn, title="high", relevance=10.0, urgency0=5.0, effort=1.0
    )
    active = queue.active(conn, limit=2)
    assert active[0].title == "boosted"


def test_active_curiosity_mode_ranks_by_curiosity(tmp_path: Path) -> None:
    conn = setup_db(tmp_path / "test.db")
    insert_source_with_scores(
        conn, title="on-goal", relevance=10.0, urgency0=5.0, effort=1.0, curiosity=3.0
    )
    insert_source_with_scores(
        conn, title="spark", relevance=2.0, urgency0=5.0, effort=1.0, curiosity=9.0
    )
    goals_active = queue.active(conn, limit=2, mode="goals")
    curiosity_active = queue.active(conn, limit=2, mode="curiosity")
    assert goals_active[0].title == "on-goal"
    assert curiosity_active[0].title == "spark"

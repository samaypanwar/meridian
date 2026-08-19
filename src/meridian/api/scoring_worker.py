from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from meridian.config import Settings
from meridian.kb import index as kb_index
from meridian.scoring import radar
from meridian.store import db
from meridian.store import repository as repo
from meridian.store.models import Scores

logger = logging.getLogger(__name__)


def _display_title_from_scores(scores: Scores) -> str | None:
    if not scores.framing:
        return None
    framing = json.loads(scores.framing)
    title = framing.get("display_title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


@lru_cache
def _goals_md() -> str:
    goals_path = Path(__file__).resolve().parents[3] / "goals.md"
    return goals_path.read_text(encoding="utf-8")


def score_source_in_background(source_id: int, settings: Settings) -> None:
    conn = db.connect(settings.db_path)
    try:
        source = repo.get_source(conn, source_id)
        if source is None or source.status != "scoring":
            return
        scores = radar.score(source, _goals_md())
        scores.source_id = source_id
        repo.insert_scores(conn, scores)
        display_title = _display_title_from_scores(scores)
        if display_title:
            conn.execute(
                "UPDATE sources SET title = ?, status = 'queued' WHERE id = ?",
                (display_title, source_id),
            )
        else:
            conn.execute(
                "UPDATE sources SET status = 'queued' WHERE id = ?", (source_id,)
            )
        conn.commit()
        source = repo.get_source(conn, source_id)
        if source and source.normalized_text and source.status == "queued":
            try:
                kb_index.index_source(conn, source_id, settings=settings)
                conn.commit()
            except Exception:
                logger.exception("Search indexing failed for source %s", source_id)
    except Exception:
        logger.exception("Radar scoring failed for source %s", source_id)
        conn.execute("UPDATE sources SET status = 'revisit' WHERE id = ?", (source_id,))
        conn.commit()
    finally:
        conn.close()

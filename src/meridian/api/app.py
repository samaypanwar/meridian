from __future__ import annotations

import json
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request

from meridian.api import schemas
from meridian.config import Settings, get_settings
from meridian.ingest import normalize, pdf, transcript, web
from meridian.scoring import queue, radar
from meridian.store import db
from meridian.store import repository as repo


@lru_cache
def _goals_md() -> str:
    goals_path = Path(__file__).resolve().parents[3] / "goals.md"
    return goals_path.read_text(encoding="utf-8")


def _fetch_normalized(ref: str, source_type: str) -> tuple[str, dict[str, Any], str | None]:
    if source_type == "web":
        text, meta = web.fetch_text(ref)
        return text, meta, ref
    if source_type in {"pdf", "arxiv"}:
        text, meta = pdf.extract_text(ref)
        return text, meta, ref
    if source_type == "youtube":
        text, meta = transcript.fetch_captions(ref)
        return text, meta, ref
    raise ValueError(f"Unsupported source type: {source_type}")


def _to_source_response(source: Any) -> schemas.SourceResponse:
    return schemas.SourceResponse(
        id=source.id,
        title=source.title,
        url=source.url,
        source_type=source.source_type,
        genre=source.genre,
        status=source.status,
        normalized_text=source.normalized_text,
    )


def _to_scores_response(scores: Any) -> schemas.ScoresResponse:
    theme = json.loads(scores.theme_breakdown) if scores.theme_breakdown else None
    framing = json.loads(scores.framing) if scores.framing else None
    reading_plan = json.loads(scores.reading_plan) if scores.reading_plan else None
    return schemas.ScoresResponse(
        relevance=scores.relevance,
        urgency0=scores.urgency0,
        effort=scores.effort,
        depth_required=scores.depth_required,
        curiosity=scores.curiosity,
        theme_breakdown=theme,
        confidence=scores.confidence,
        framing=framing,
        reading_plan=reading_plan,
    )


def _detail(source: Any, scores: Any | None) -> schemas.SourceDetailResponse:
    return schemas.SourceDetailResponse(
        source=_to_source_response(source),
        scores=_to_scores_response(scores) if scores else None,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        conn = db.connect(settings.db_path)
        db.init_schema(conn)
        app.state.conn = conn
        app.state.settings = settings
        yield
        conn.close()

    app = FastAPI(title="Meridian", lifespan=lifespan)

    def get_conn(request: Request) -> Any:
        return request.app.state.conn

    @app.post("/sources", response_model=schemas.SourceDetailResponse)
    def add_source(body: schemas.AddSourceRequest, conn: Any = Depends(get_conn)) -> Any:
        source = normalize.ingest(body.ref)
        try:
            text, meta, url = _fetch_normalized(body.ref, source.source_type)
            source.normalized_text = text
            source.length_meta = json.dumps(meta)
            source.url = url
            source.title = meta.get("title") or body.ref
        except Exception:
            source.title = body.ref
        saved = repo.insert_source(conn, source)
        scores = radar.score(saved, _goals_md())
        scores.source_id = saved.id or 0
        saved_scores = repo.insert_scores(conn, scores)
        return _detail(saved, saved_scores)

    @app.get("/queue", response_model=schemas.QueueResponse)
    def get_queue(conn: Any = Depends(get_conn)) -> schemas.QueueResponse:
        active = queue.active(conn)
        items = []
        for source in active:
            scores = repo.get_scores(conn, source.id or 0)
            items.append(_detail(source, scores))
        return schemas.QueueResponse(active=items)

    @app.get("/sources/{source_id}", response_model=schemas.SourceDetailResponse)
    def get_source(source_id: int, conn: Any = Depends(get_conn)) -> Any:
        bundle = repo.source_with_scores(conn, source_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Source not found")
        return _detail(bundle["source"], bundle["scores"])

    return app


app = create_app()

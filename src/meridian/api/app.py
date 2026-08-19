from __future__ import annotations

import json
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from meridian.api import capture as capture_flow
from meridian.api import schemas
from meridian.config import Settings, get_settings
from meridian.ingest import normalize, pdf, transcript, web
from meridian.kb import index, query
from meridian.review import questions, scheduler
from meridian.scoring import indicators, queue, radar
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_conn(request: Request) -> Any:
        return request.app.state.conn

    def get_settings_from_app(request: Request) -> Settings:
        return request.app.state.settings

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

    @app.post("/sources/{source_id}/capture")
    def capture_preview_route(
        source_id: int,
        body: schemas.CaptureRequest,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> dict[str, Any]:
        if not body.reflection.strip():
            conn.execute("UPDATE sources SET status = 'revisit' WHERE id = ?", (source_id,))
            conn.commit()
            return {"preview": "SHALLOW", "shallow": True}
        return capture_flow.draft_capture(
            source_id, body.reflection, conn=conn, settings=settings, goals_md=_goals_md()
        )

    @app.post("/sources/{source_id}/capture/approve")
    def capture_approve_route(
        source_id: int,
        body: schemas.CaptureApproveRequest,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> dict[str, str]:
        result = capture_flow.approve_capture(
            source_id, body.preview, conn=conn, settings=settings
        )
        if result["note_path"]:
            index.add_note(conn, result["note_path"], settings=settings)
            conn.commit()
            review_row = conn.execute(
                "SELECT id FROM reviews WHERE note_path = ? ORDER BY id DESC LIMIT 1",
                (result["note_path"],),
            ).fetchone()
            if review_row:
                generated = questions.generate(result["note_path"])
                conn.execute(
                    "UPDATE reviews SET question = ? WHERE id = ?",
                    (generated["question"], review_row["id"]),
                )
                conn.commit()
        return result

    @app.get("/kb/query")
    def kb_query_route(
        q: str = Query(...),
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> dict[str, Any]:
        answer = query.believe(conn, q, settings=settings)
        return {"text": answer.text, "citations": answer.citations}

    @app.get("/reviews/due")
    def reviews_due_route(conn: Any = Depends(get_conn)) -> dict[str, Any]:
        due = scheduler.due(conn)
        return {
            "reviews": [
                {
                    "id": r.id,
                    "question": r.question,
                    "note_path": r.note_path,
                    "source_id": r.source_id,
                }
                for r in due
            ]
        }

    @app.post("/reviews/{review_id}/grade")
    def grade_review_route(
        review_id: int,
        body: schemas.GradeRequest,
        conn: Any = Depends(get_conn),
    ) -> dict[str, str]:
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Review not found")

        history = json.loads(row["history"] or "[]")
        history.append(
            {"date": datetime.now(timezone.utc).isoformat(), "grade": body.grade}
        )
        interval, ease = scheduler.next_interval(
            row["interval_days"], row["ease"], body.grade
        )
        due_at = datetime.now(timezone.utc) + timedelta(days=interval)
        conn.execute(
            """
            UPDATE reviews
            SET interval_days = ?, ease = ?, due_at = ?, history = ?
            WHERE id = ?
            """,
            (interval, ease, due_at.isoformat(), json.dumps(history), review_id),
        )

        misses = sum(1 for h in history if h.get("grade") == "missed")
        status = "graded"
        if misses >= 2 and row["source_id"]:
            conn.execute(
                "UPDATE sources SET status = 'revisit' WHERE id = ?",
                (row["source_id"],),
            )
            status = "revisit"
        conn.commit()
        return {"status": status}

    @app.get("/goals")
    def goals_route(
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> dict[str, Any]:
        return {
            "goals_md": _goals_md(),
            "indicators": indicators.for_cycle(conn, settings.vault_path),
        }

    return app


app = create_app()

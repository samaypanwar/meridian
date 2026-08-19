from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from meridian.api import capture as capture_flow
from meridian.api import schemas
from meridian.api.scoring_worker import score_source_in_background
from meridian.api.source_ops import (
    apply_fetched_content,
    apply_pasted_transcript,
    mark_for_rescore,
    ref_for_source,
    update_source_record,
)
from meridian.config import Settings, get_settings
from meridian.ingest import normalize, transcript
from meridian.ingest.fetch import fetch_normalized
from meridian.ingest.titles import clean_extracted_title
from meridian.kb import index, query
from meridian.review import questions, scheduler
from meridian.scoring import indicators, queue
from meridian.store import db
from meridian.store import repository as repo


@lru_cache
def _goals_md() -> str:
    goals_path = Path(__file__).resolve().parents[3] / "goals.md"
    return goals_path.read_text(encoding="utf-8")


logger = logging.getLogger(__name__)

_YOUTUBE_DEGRADED = frozenset({"blocked", "disabled", "missing", "empty"})


def _apply_ingested_content(
    source: Any, *, text: str, meta: dict[str, Any], url: str | None, ref: str
) -> None:
    source.length_meta = json.dumps(meta)
    source.url = url
    source.title = meta.get("title") or ref
    if source.title:
        source.title = clean_extracted_title(source.title, source.url)
    if meta.get("author"):
        source.author = meta["author"]
    if text.strip():
        source.normalized_text = text
        return
    if (
        source.source_type == "youtube"
        and meta.get("transcript_status") in _YOUTUBE_DEGRADED
    ):
        source.normalized_text = None
        return
    raise ValueError("No readable text extracted from this link")


def _ingest_status_message(
    settings: Settings, source: Any, meta: dict[str, Any]
) -> str:
    transcript_status = meta.get("transcript_status")
    if source.source_type != "youtube" or transcript_status not in _YOUTUBE_DEGRADED:
        return (
            f"Ingested. Radar pass running via {settings.llm_model} against goals.md."
        )
    if transcript_status == "blocked":
        return (
            f"YouTube blocked the transcript fetch. Radar pass running from title/metadata only "
            f"via {settings.llm_model} (expect low confidence). Paste a transcript on the source "
            "page for a full score."
        )
    if transcript_status == "disabled":
        return (
            f"This video has no captions. Radar pass running from title/metadata only via "
            f"{settings.llm_model} (expect low confidence)."
        )
    return (
        f"No transcript available. Radar pass running from title/metadata only via "
        f"{settings.llm_model} (expect low confidence)."
    )


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


def _accepted_response(
    saved: Any, settings: Settings, message: str
) -> schemas.AddSourceResponse:
    return schemas.AddSourceResponse(
        source=_to_source_response(saved),
        scores=None,
        scoring_model=settings.llm_model,
        status_message=message,
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

    @app.post("/sources", response_model=schemas.AddSourceResponse, status_code=202)
    def add_source(
        body: schemas.AddSourceRequest,
        background_tasks: BackgroundTasks,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> schemas.AddSourceResponse:
        source = normalize.ingest(body.ref)
        try:
            pasted = (body.transcript or "").strip()
            if pasted:
                if source.source_type != "youtube":
                    raise HTTPException(
                        status_code=422,
                        detail="Transcript paste is only supported for YouTube links.",
                    )
                meta = transcript.fetch_video_meta(body.ref)
                meta.update(
                    {
                        "words": len(pasted.split()),
                        "transcript_status": "pasted",
                        "engine": "manual",
                    }
                )
                _apply_ingested_content(
                    source,
                    text=pasted,
                    meta=meta,
                    url=body.ref,
                    ref=body.ref,
                )
            else:
                text, meta, url = fetch_normalized(body.ref, source.source_type)
                _apply_ingested_content(
                    source,
                    text=text,
                    meta=meta,
                    url=url,
                    ref=body.ref,
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Ingest failed for %s", body.ref)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Could not fetch readable text from this link ({exc}). "
                    "Meridian needs the article body to score it against your goals."
                ),
            ) from exc
        source.status = "scoring"
        saved = repo.insert_source(conn, source)
        background_tasks.add_task(score_source_in_background, saved.id or 0, settings)
        meta = json.loads(source.length_meta or "{}")
        return _accepted_response(
            saved,
            settings,
            _ingest_status_message(settings, source, meta),
        )

    @app.post(
        "/sources/{source_id}/refetch",
        response_model=schemas.AddSourceResponse,
        status_code=202,
    )
    def refetch_source(
        source_id: int,
        background_tasks: BackgroundTasks,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> schemas.AddSourceResponse:
        source = repo.get_source(conn, source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        try:
            ref = ref_for_source(source)
            source = apply_fetched_content(source, ref)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Re-fetch failed for source %s", source_id)
            raise HTTPException(
                status_code=422,
                detail=f"Could not re-fetch readable text ({exc}).",
            ) from exc
        mark_for_rescore(conn, source_id)
        update_source_record(conn, source)
        background_tasks.add_task(score_source_in_background, source_id, settings)
        refreshed = repo.get_source(conn, source_id)
        assert refreshed is not None
        meta = json.loads(refreshed.length_meta or "{}")
        return _accepted_response(
            refreshed,
            settings,
            _ingest_status_message(settings, refreshed, meta).replace(
                "Ingested.", "Re-fetched."
            ),
        )

    @app.post(
        "/sources/{source_id}/transcript",
        response_model=schemas.AddSourceResponse,
        status_code=202,
    )
    def paste_transcript(
        source_id: int,
        body: schemas.TranscriptRequest,
        background_tasks: BackgroundTasks,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> schemas.AddSourceResponse:
        source = repo.get_source(conn, source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        try:
            source = apply_pasted_transcript(source, body.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        mark_for_rescore(conn, source_id)
        update_source_record(conn, source)
        background_tasks.add_task(score_source_in_background, source_id, settings)
        refreshed = repo.get_source(conn, source_id)
        assert refreshed is not None
        return _accepted_response(
            refreshed,
            settings,
            f"Transcript saved. Radar pass running via {settings.llm_model} against goals.md.",
        )

    @app.post(
        "/sources/{source_id}/rescore",
        response_model=schemas.AddSourceResponse,
        status_code=202,
    )
    def rescore_source(
        source_id: int,
        background_tasks: BackgroundTasks,
        conn: Any = Depends(get_conn),
        settings: Settings = Depends(get_settings_from_app),
    ) -> schemas.AddSourceResponse:
        source = repo.get_source(conn, source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")
        if not source.normalized_text:
            raise HTTPException(
                status_code=422,
                detail="No stored text to score. Re-fetch or paste a transcript first.",
            )
        mark_for_rescore(conn, source_id)
        background_tasks.add_task(score_source_in_background, source_id, settings)
        pending = repo.get_source(conn, source_id)
        assert pending is not None
        return _accepted_response(
            pending,
            settings,
            f"Re-scoring stored text via {settings.llm_model} against goals.md.",
        )

    @app.get("/queue", response_model=schemas.QueueResponse)
    def get_queue(conn: Any = Depends(get_conn)) -> schemas.QueueResponse:
        active = queue.active(conn)
        items = []
        for source in active:
            scores = repo.get_scores(conn, source.id or 0)
            items.append(_detail(source, scores))
        pending_items = [
            _detail(source, repo.get_scores(conn, source.id or 0))
            for source in queue.pending(conn)
        ]
        backlog_items = [
            _detail(source, repo.get_scores(conn, source.id or 0))
            for source in queue.backlog(conn)
        ]
        return schemas.QueueResponse(
            active=items, pending=pending_items, backlog=backlog_items
        )

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
            conn.execute(
                "UPDATE sources SET status = 'revisit' WHERE id = ?", (source_id,)
            )
            conn.commit()
            return {"preview": "SHALLOW", "shallow": True}
        return capture_flow.draft_capture(
            source_id,
            body.reflection,
            conn=conn,
            settings=settings,
            goals_md=_goals_md(),
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
        row = conn.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
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

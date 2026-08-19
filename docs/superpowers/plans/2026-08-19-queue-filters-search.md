# Queue filters + unified search — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add medium/theme filtering on Home and unified semantic search over queue sources + vault captures.

**Architecture:** Derive `platform` from URL at read time; client-side filter/sort for medium + theme; extend existing `emb`/`emb_meta` to index source text on ingest; new `GET /search` combines queue vector hits with existing KB synthesis.

**Tech Stack:** FastAPI, React/Vite, sqlite-vec, sentence-transformers (existing), TypeScript vitest for frontend filter tests.

## Global Constraints

- Theme include rule: `theme_breakdown[theme] > 0` only.
- Theme sort: descending by selected theme score; overrides goals/curiosity sort while active.
- Search results in separate panel; do not replace filtered card list.
- LessWrong remains `source_type=web`; UI uses `platform=lesswrong`.
- Persist filter state in `localStorage` key `meridian-queue-filters`.
- Search triggers on submit only (Enter / button).

---

## File map

| File | Action |
|------|--------|
| `src/meridian/ingest/platform.py` | **Create** — `platform_for_source(source)` |
| `tests/ingest/test_platform.py` | **Create** |
| `src/meridian/api/schemas.py` | Add optional `platform` on `SourceResponse` |
| `src/meridian/api/app.py` | Populate `platform`; add `GET /search` |
| `src/meridian/kb/index.py` | Add `index_source`, extend `reindex` |
| `src/meridian/kb/search.py` | **Create** — unified search orchestration |
| `src/meridian/api/scoring_worker.py` | Call `index_source` after queue |
| `tests/kb/test_source_index.py` | **Create** |
| `tests/api/test_search.py` | **Create** |
| `frontend/src/lib/platform.ts` | **Create** |
| `frontend/src/lib/queueFilters.ts` | **Create** |
| `frontend/src/lib/queueFilters.test.ts` | **Create** |
| `frontend/src/components/QueueFilterBar.tsx` | **Create** |
| `frontend/src/components/QueueSearchResults.tsx` | **Create** |
| `frontend/src/pages/Home.tsx` | Wire filters + search |
| `frontend/src/api.ts` | Add `search()` |
| `frontend/src/index.css` | Filter bar + search panel styles |

---

## Phase 1 — Medium + theme filters (client-only)

### Task 1: Platform helper (backend + frontend)

**Files:** `src/meridian/ingest/platform.py`, `tests/ingest/test_platform.py`, `frontend/src/lib/platform.ts`

- [ ] Write failing tests: youtube URL, lesswrong `/posts/`, alignment forum, plain web, pdf, arxiv.
- [ ] Implement `platform_for_source(url, source_type) -> str`.
- [ ] Mirror logic in `frontend/src/lib/platform.ts`.
- [ ] Run `poetry run pytest tests/ingest/test_platform.py -q`.

### Task 2: Expose platform on API responses

**Files:** `src/meridian/api/schemas.py`, `src/meridian/api/app.py`

- [ ] Add `platform: str | None` to `SourceResponse`.
- [ ] Set in `_to_source_response()` via `platform_for_source`.
- [ ] Extend `frontend/src/api.ts` `Source` interface with `platform?`.
- [ ] Run API route tests: `poetry run pytest tests/api/test_routes.py -q`.

### Task 3: Queue filter/sort library

**Files:** `frontend/src/lib/queueFilters.ts`, `frontend/src/lib/queueFilters.test.ts`

- [ ] Implement `filterByMedium(items, selectedMedia: Platform[] | 'all')`.
- [ ] Implement `applyThemeSelection(items, theme: string | 'all')` — filter >0, sort desc.
- [ ] Write vitest tests for combined medium + theme.
- [ ] Run `cd frontend && npm test` (or add vitest script if missing).

### Task 4: QueueFilterBar UI

**Files:** `frontend/src/components/QueueFilterBar.tsx`, `frontend/src/index.css`, `frontend/src/pages/Home.tsx`

- [ ] Fetch themes from goals (reuse `getGoals` + `parseGoals` or parse themes helper).
- [ ] Render medium chips + theme chips with counts from current queue data.
- [ ] Persist selection to `localStorage`.
- [ ] Apply filters to `active` and `backlog` before pagination in `Home.tsx`.
- [ ] Manual check: YouTube-only, theme re-rank, All restores default sort.

**Phase 1 commit:** `feat(ui): queue medium and theme filters`

---

## Phase 2 — Index queue sources + search API

### Task 5: Index source text into emb

**Files:** `src/meridian/kb/index.py`, `tests/kb/test_source_index.py`

- [ ] Add `chunk_source_text(text: str) -> list[str]` (paragraph split, max ~800 chars).
- [ ] Add `index_source(conn, source_id, text, framing_json, settings) -> int`.
- [ ] Delete existing emb rows for `source_id` before re-indexing that source.
- [ ] Extend `reindex()` to loop queued/captured sources with `normalized_text`.
- [ ] Write tests with stub embed model.

### Task 6: Hook index on ingest

**Files:** `src/meridian/api/scoring_worker.py`

- [ ] After status → `queued`, if `normalized_text`, call `index_source`.
- [ ] Run scoring worker tests.

### Task 7: Unified search endpoint

**Files:** `src/meridian/kb/search.py`, `src/meridian/api/app.py`, `tests/api/test_search.py`

- [ ] Implement `search.unified(conn, q, settings) -> UnifiedSearchResult`.
- [ ] Queue leg: vector search where `source_id IS NOT NULL`, dedupe by source, join scores.
- [ ] Captures leg: delegate to `query.believe()`.
- [ ] Add `GET /search?q=` route.
- [ ] Tests: empty index, queue-only, captures-only, both.

**Phase 2 commit:** `feat(api): index queue sources and unified search`

---

## Phase 3 — Search UI on Home

### Task 8: API client + results panel

**Files:** `frontend/src/api.ts`, `frontend/src/components/QueueSearchResults.tsx`, `frontend/src/index.css`

- [ ] Add `searchQuery(q: string)` typing response.
- [ ] Build results panel: queue section (SourceCard links) + captures section (answer + citations).
- [ ] Empty/loading/error states.

### Task 9: Wire Home search box

**Files:** `frontend/src/pages/Home.tsx`, `frontend/src/components/QueueFilterBar.tsx`

- [ ] Add search input to filter bar (or adjacent row per spec layout).
- [ ] On submit, call `searchQuery`; show `QueueSearchResults` below filter bar.
- [ ] Clear search button; does not reset medium/theme filters.
- [ ] Run `npm run build`.

**Phase 3 commit:** `feat(ui): unified queue and capture search on Home`

---

## Verification checklist

- [ ] `poetry run pytest -q` — all pass
- [ ] `cd frontend && npm run build` — pass
- [ ] Ingest YouTube + LessWrong + web; medium chips filter correctly
- [ ] Select theme; order changes by theme score; 0-score items hidden
- [ ] Search returns queue + capture sections when both exist
- [ ] Reindex populates source embeddings for existing queue

---

## Notes for implementer

- Do not add minimum theme score threshold (e.g. 4) — user confirmed `> 0` only.
- Knowledge page `/kb/query` stays; Home search is the primary unified entry.
- If vitest is not configured, add minimal vitest config in Phase 1 Task 3 only.

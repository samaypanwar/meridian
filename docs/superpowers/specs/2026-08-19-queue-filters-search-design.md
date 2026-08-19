# Queue filters + unified search — design spec

**Date:** 2026-08-19  
**Status:** Approved  
**Scope:** Home page (Active Queue) — medium filters, theme re-rank, unified RAG search

---

## Problem

After bulk ingest, the queue grows faster than linear scrolling. Users need to:

1. Slice by **medium** (YouTube, LessWrong, web, PDF, arXiv).
2. Re-rank by **theme** from `goals.md` (any non-zero theme score).
3. **Search** across both the queue (ingested sources) and vault captures in one query.

Ranking alone (goals / curiosity mode) is not enough for navigation.

---

## Goals

- Filter the visible queue by platform/medium with chip UI.
- Select a theme to show only sources with `theme_breakdown[theme] > 0`, sorted by that theme score descending.
- One search box under Active Queue that returns **two labeled sections**: queue matches + capture matches.
- Filters and search compose without fighting each other.

## Non-goals (this cycle)

- Server-side queue pagination/filter API (client-side is fine while queue < ~100).
- Genre row (paper / video / nonfiction) — defer.
- Search-as-you-type on every keystroke — submit on button/Enter only.
- Changing Knowledge page layout (Home gets unified search; Knowledge page can stay or link later).

---

## UX

### Layout (Home, below hero add bar, above queue cards)

```
Medium:  [All] [YouTube] [LessWrong] [Web] [PDF] [ArXiv]
Theme:   [All] [agentic-harnesses] [data-science] [rl] …
Search:  [ …                                           ] [Search]
```

### Medium filters

Multi-select OR within the group. AND with theme selection and with search results scope.

| Chip | Match rule |
|------|------------|
| All | No medium filter |
| YouTube | `source.source_type === 'youtube'` |
| LessWrong | URL host ∈ `{lesswrong.com, www.lesswrong.com, alignmentforum.org, www.alignmentforum.org}` |
| PDF | `source.source_type === 'pdf'` |
| ArXiv | `source.source_type === 'arxiv'` |
| Web | `source.source_type === 'web'` AND NOT LessWrong host |

Show optional count badge per chip when count > 0.

### Theme selection

- Theme list from `goals.md` (reuse `goalsParse.ts` / Goals page themes).
- **All:** normal queue ranking (`goals` or `curiosity` mode per toggle).
- **Specific theme:**
  - **Include:** `theme_breakdown[theme] > 0` only.
  - **Sort:** descending by `theme_breakdown[theme]`.
  - Overrides goals/curiosity sort while selected.
- Applies to **active + backlog** when backlog is expanded.

### Unified search

- Trigger: Submit (button or Enter), not live debounce.
- **Search corpus (queue):** title, URL, genre, platform, all framing fields (`display_title`, `point`, `matters_for_goals`, `where_to_focus`, `why_now`, `skip_if`), theme keys with score > 0, and full `normalized_text`. **Not title-only.**
- Phase 1: client-side keyword search over this corpus (`buildSearchableText`).
- Phase 2+: same corpus embedded for vector RAG (`src/meridian/kb/searchable.py` mirrors frontend).
- **Does not** narrow the card list — results appear in a **separate panel below** the filter bar (and above or below queue cards; default: between filter bar and queue cards when results exist).
- Response sections (always labeled):
  1. **In your queue** — `SourceDetail[]` from vector search over indexed source text.
  2. **Already captured** — same shape as `/kb/query` (answer text + citation note paths).

Empty states:

- No queue index rows → queue section: “No indexed sources yet” + note that ingest/reindex will populate.
- No captures → capture section omitted or “No captures yet”.

### Interaction matrix

| Active | Card list | Search panel |
|--------|-----------|--------------|
| Medium chips only | Filtered | Hidden |
| Theme chip only | Filtered + re-ranked | Hidden |
| Search submitted | Still uses medium/theme filters on queue section only | Visible |
| Clear search | Filters remain | Hidden |

Persist medium + theme selection in `localStorage` (`meridian-queue-filters`).

---

## Data model

### Platform (derived, not stored)

Add helper `platform(source: Source) -> string`:

- `youtube` | `lesswrong` | `pdf` | `arxiv` | `web`

Expose on API responses as optional `platform` on `SourceResponse` for UI consistency (computed in backend from URL + `source_type`).

### Queue embeddings

Extend existing `emb` / `emb_meta` tables (no schema migration if `emb_meta.source_id` already exists — verify).

Index per source on ingest success (status → `queued`):

- Chunk `normalized_text` (simple paragraph/sentence chunks, ~500–800 chars).
- Optionally prepend framing `point` + `matters_for_goals` as a high-weight chunk.
- Store `emb_meta.source_id`, `chunk_text`, `note_path` null.

Reindex endpoint (`POST /reindex` or existing) must:

1. Clear and rebuild vault capture chunks (existing behavior).
2. Clear and rebuild queue source chunks (new).

---

## API

### `GET /search?q=...&limit=10`

Returns:

```json
{
  "query": "agent harness orchestration",
  "queue": [ /* SourceDetail[] */ ],
  "captures": {
    "text": "…synthesized answer…",
    "citations": ["path/to/note.md"]
  }
}
```

Implementation:

- Embed query once.
- Queue: vector search `emb_meta` where `source_id IS NOT NULL`, join `sources` + `scores`, return top-k distinct sources.
- Captures: existing `kb.query.believe()` logic (top-k chunks → LLM synthesis).

Optional query params later: `medium`, `theme` — **not v1** (client filters queue section of card list only; search panel queue hits can be client-filtered post-fetch if cheap).

### Goals endpoint

Already returns `goals_md`. Frontend parses themes — no change required.

---

## Frontend components

| Component | Responsibility |
|-----------|----------------|
| `QueueFilterBar` | Medium chips, theme chips, search input |
| `QueueSearchResults` | Two-section results panel |
| `lib/platform.ts` | `platformFromSource(source)` — mirror backend rules for client-side filter |
| `lib/queueFilters.ts` | Apply medium filter + theme filter/sort to `SourceDetail[]` |
| `Home.tsx` | Wire filter state, search submit, persist localStorage |

Reuse `SourceCard` for queue search hits. Reuse Knowledge citation list styling for captures section.

---

## Testing

### Backend

- `platform()` unit tests for each URL type.
- Source indexing: after mock ingest, `emb_meta` has rows with `source_id`.
- `/search` returns both sections when data exists; empty gracefully.

### Frontend

- `queueFilters.test.ts`: medium filter, theme filter (>0), theme sort order.
- Manual: compose YouTube + theme + search.

---

## Phasing

| Phase | Deliverable |
|-------|-------------|
| **1** | `platform` helper, filter bar UI, client-side medium + theme filter/sort |
| **2** | Index sources on ingest + reindex; `GET /search` |
| **3** | Search box + results panel on Home; polish (counts, localStorage, empty states) |

Each phase is shippable independently.

---

## Open decisions (resolved)

| Question | Decision |
|----------|----------|
| RAG scope | Both queue + captures, split sections |
| Theme filter threshold | Any `theme_breakdown[theme] > 0` |
| Theme behavior | Filter non-zero + sort by theme score |
| Search vs card list | Separate panel; card list still driven by filters only |
| LessWrong storage | Derive `platform=lesswrong` from URL; keep `source_type=web` |

---

## Success criteria

- User can show only YouTube items in queue.
- User can select `frontier/agentic-harnesses` and see highest-fit sources first.
- User can search “policy gradient variance” and see queue sources + vault captures in one flow.
- No regression to goals/curiosity ranking when All themes + All medium selected.

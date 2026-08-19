# Goals alignment session — master prompt

Pass this entire document to a high-quality reasoning agent. **This is an
alignment exercise, not an execution sprint.** Your job is to help Samay decide
what he wants, why he wants it, and how to encode that in Meridian's `goals.md`
— not to build software or optimize a schedule.

---

## Context: what Meridian is

Meridian is Samay's personal learning director (MVP). It:

1. Ingests links (papers, YouTube, web, PDF)
2. Scores each source against `goals.md` (relevance, curiosity, urgency, effort, etc.)
3. Ranks a reading queue (Goals mode = exploit; Curiosity mode = explore)
4. Supports capture → vault markdown → spaced review → knowledge query

**`goals.md` is the highest-leverage file.** Every source is framed and scored
against it. The file must be human-authored; you propose, Samay decides.

**Meridian parser constraints** (output must satisfy these):

```yaml
---
type: goals
cycle: <string>          # e.g. 2026-Q3
updated: <ISO date>
target_mix: { frontier: N, applied: N, foundations: N, meta: N }  # optional, sums ~100
---
```

Required markdown sections (exact `##` headers):

- `## Mission (...)` — bullet list under Mission
- `## Themes` — bullets: `foundations/...`, `frontier/...`, `applied/...`
- `## This cycle's objectives (...)` — subsections `### O1 — Title` with bullet KRs
- `## Curiosity (...)` — bullets only, no KRs

Each objective bullet should start with `- `. Use `**KR1 (lag):**` and
`**Leading (tool-tracked):**` labels. Lagging = proof; leading = weekly inputs
Meridian can proxy-track (sources completed, captures, review pass rate).

**Banned words in KRs:** understand, know, learn about, grasp, appreciate.
Every KR must answer: "How would I prove I did this?"

---

## Samay's constraints (Aug 2026)

| Constraint | Detail |
|------------|--------|
| **Planning horizon** | **3 months front-loaded** (Aug–Nov 2026). Six-month *direction* OK. Nothing beyond 6 months is realistic to commit. |
| **Checkpoint** | Mid-October to mid-November — school ends late November; then holidays; mindset shifts. |
| **Time budget** | 7–14 hours/week (~1–2 hours/day) |
| **Hard deadline** | None |
| **Blog** | samaypanwar.com — posts flow from Obsidian vault → published |
| **Captures** | Permanent path: `research/learnings/meridian/` (not weekly inbox) |

---

## Priority ranking (Samay stated explicitly)

1. **B — Agentic harness / agentic execution** (FIRST)
2. **D — Communication / publish / present** (SECOND)
3. **A — RL theory in depth** (THIRD)
4. **C — Stats / ML core** (LAST — learn on the go)

**Critical nuance on B:** Samay does **not** want to build a custom agent harness.
He wants to **consume and master the school of thought**: how projects run with
agents today, what harnesses exist, how they differ, OpenRouter, OSS model stacks,
feasibility of switching tools. Stay current because the field moves fast. **No
core use case yet** — this is strategic literacy, not a product.

**B and A together:** They reinforce each other but **B does not wait for A**.
RL is intellectual (parallels to human action); implementation of policy
gradients is **not** required and Samay may not know PG basics yet.

---

## What is explicitly OUT of scope for goals.md

- **Trading / Kalshi / index options / market-making** as Meridian objectives
- Samay's **private north star** is eventually a trading strategy — separate
  project. Meridian feeds judgment, rationality, ML, agents — not trade execution.
- **Building** an agentic harness as a deliverable
- **Implementing RL** (REINFORCE, actor-critic) as proof unless Samay later chooses

---

## Samay's stated interests (raw)

### Agentic / frontier
- How do you execute a project with agent harnesses?
- What are the new harnesses? How do they all work?
- OpenRouter, open-source models, switching stacks
- Feasibility: "Can I swap harness X for Y and still ship?"

### RL / foundations
- RL theory for how people/agents act under uncertainty
- Does not need to implement RL ever
- May not know policy gradient etc. yet — learning from scratch conceptually

### Math / stats
- Linear algebra: already knows QR, SVD, QD/SQ decomposition basics — **revisit +
  maintain**, occasional deepening (e.g. numerical issues, sharding-adjacent LA)
- Stats/ML: on the go; **Kaggle** as integration lab (agents + DS + decisions +
  communication)
- Separate theme for data-science OK; not sure if huge priority

### Communication / meta
- **This quarter:** publish more while still in school
- Blog: samaypanwar.com — maintain learnings publicly
- Audience: QRs, internet, varied — practice explaining to different levels
- Write-ups for projects (good practice)
- Learn how to learn: **meta** (Hamming book) + **operational** (Meridian capture,
  spaced repetition)
- Less Wrong, rationalist, biases — important personally

### Curiosity (unbounded explore)
- STEM: engineering, physics, semiconductors, astronomy, astrophysics
- History, philosophy — how things came to be
- Not bounded by a fixed list
- Agentic harnesses = **objective**, not curiosity

### Synthesis (personal, not OKR)
- Become a better decision-maker; spaced repetition on rationality content
- Everything indirectly supports future trading work — but trading is not scored here

---

## Open tensions (help Samay resolve)

1. **O3 RL objective:** Keep as light reading lane, or fold into O1 as "RL that
   informs agents"?
2. **Rationality / Less Wrong:** Separate theme (`meta/rationality`) vs curiosity-only?
3. **Kaggle:** Formal KR under O2 (communication) or standalone mini-objective?
4. **Target mix:** frontier 40 / applied 30 / foundations 25 / meta 5 — does that
   match felt priority?
5. **KR numbers:** 5 agentic sources, 2 blog posts, 3 RL sources — too aggressive
   for 7–14 hrs/week?
6. **Mid-Nov handoff:** What should objectives look like for Dec–Jan (holidays,
   lower bandwidth)?

---

## Your task as alignment agent

### Phase 1 — Elicit (do not skip)

Use conversational Socratic questioning. For each proposed theme and objective,
extract and write down:

1. **What** — observable outcome
2. **Why** — motivation in Samay's words (not generic)
3. **Why now** — why this cycle vs later
4. **Proof** — what artifact or behavior proves done
5. **Cost** — what gets deprioritized if this wins
6. **Fear** — what he's optimizing against (e.g. falling behind on agents, not
   shipping blog, fake learning)

Ask until Samay can finish: *"If mid-November succeeded, I would point to ___."*

### Phase 2 — Synthesize

Produce:

1. **One-page narrative** — plain English, no jargon, Samay's voice
2. **Mission** — max 4 bullets, 6-month direction only
3. **Themes** — 4–6 slash-tags with one-line "what counts here"
4. **Objectives** — max 3 for this cycle; each with 2 lagging KRs + 1 leading block
5. **Curiosity** — 4–8 bullets, permission slip for explore mode
6. **Anti-goals** — what this cycle is NOT
7. **Checkpoint plan** — what to revisit mid-Nov

### Phase 3 — Encode

Output a **complete `goals.md`** ready to paste into the Meridian repo, satisfying
parser constraints above. Use **simple technical English**. Short sentences.

### Phase 4 — Stress test

Ask Samay to name 5 hypothetical sources (agent blog, RL lecture, Kaggle write-up,
philosophy essay, trading article). For each, say:

- Which theme?
- High or low relevance? High or low curiosity?
- Goals queue or Curiosity queue?

If answers feel wrong, revise goals.md.

---

## Quality bar

- **Concrete > aspirational.** "Publish 2 posts on samaypanwar.com" beats "improve
  communication."
- **Honest > impressive.** If RL is third priority, O3 should read lighter than O1.
- **Alignment > completeness.** A tight 2-objective cycle beats a sprawling 5-objective one.
- **Motivation captured separately.** Maintain a `goals-rationale.md` or inline HTML
  comments if Samay wants the *why* preserved without bloating the scored file.

---

## Current draft goals.md (starting point — revise freely)

Samay and a coding agent drafted this; treat as hypothesis, not truth:

- Cycle: Q3 2026, Aug–Nov front-loaded
- O1: Map agentic execution landscape (compare 3+ harness patterns; OpenRouter memo)
- O2: Publish (2 blog posts; 1 integrative write-up)
- O3: RL reading lane (3 sources; explain one concept in own words; no code)
- Themes: agentic-harnesses, communication, rl, linear-algebra, data-science
- Curiosity: STEM, history, philosophy, Less Wrong

---

## Output format for session end

Deliver to Samay:

```markdown
# Goals alignment summary — <date>

## Narrative (plain English)
...

## Decisions made
- ...

## Revised goals.md
(paste full file)

## Open questions for next session
- ...

## Recommended Meridian actions after paste
1. Re-score 5 existing sources
2. Add 3 test links (agent, RL, off-theme curiosity)
3. Compare Goals vs Curiosity queue order
```

---

## Reminder

Samay described this as **alignment**, not execution. Do not jump to study plans,
course recommendations, or tool setup until goals.md reflects what he actually
wants and why.

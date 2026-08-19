import { useNavigate, useParams } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import RadarChart, { accessibilityScore } from "../components/RadarChart";
import ReadingPlan from "../components/ReadingPlan";
import {
  getSource,
  pasteTranscript,
  priorityScore,
  refetchSource,
  rescoreSource,
  sleep,
  type Scores,
  type SourceDetail,
} from "../api";

function displayTitle(detail: SourceDetail | null): string {
  if (!detail) return "";
  const framingTitle = detail.scores?.framing?.display_title;
  if (typeof framingTitle === "string" && framingTitle.trim()) {
    return framingTitle.trim();
  }
  return detail.source.title ?? detail.source.url ?? "Untitled source";
}

function scoreRadarAxes(scores: Scores) {
  return {
    labels: ["Relevance", "Urgency", "Depth", "Curiosity", "Accessibility"],
    values: [
      scores.relevance ?? 0,
      scores.urgency0 ?? 0,
      scores.depth_required ?? 0,
      scores.curiosity ?? 0,
      accessibilityScore(scores.effort),
    ],
  };
}

function themeRadarAxes(themeBreakdown: Record<string, number>) {
  const entries = Object.entries(themeBreakdown).sort((a, b) => b[1] - a[1]);
  return {
    labels: entries.map(([theme]) => theme.split("/").pop() ?? theme),
    values: entries.map(([, value]) => value),
    fullLabels: entries.map(([theme]) => theme),
  };
}

export default function SourceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SourceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<"refetch" | "rescore" | "transcript" | null>(null);
  const [transcriptDraft, setTranscriptDraft] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    const data = await getSource(Number(id));
    setDetail(data);
    return data;
  }, [id]);

  useEffect(() => {
    load().catch((e) => setError(String(e)));
  }, [load]);

  async function pollWhileScoring() {
    if (!id) return;
    for (let i = 0; i < 90; i += 1) {
      await sleep(2000);
      const data = await load();
      if (data?.source.status !== "scoring" && data?.scores) {
        setStatusMessage("Radar pass complete.");
        setBusy(null);
        return;
      }
      if (data?.source.status === "revisit" && !data.scores) {
        setError("Scoring failed. Try re-fetch again.");
        setBusy(null);
        return;
      }
    }
    setStatusMessage("Scoring is still running…");
    setBusy(null);
  }

  async function onRefetch() {
    if (!id) return;
    setBusy("refetch");
    setError(null);
    setStatusMessage(null);
    try {
      const resp = await refetchSource(Number(id));
      setStatusMessage(resp.status_message);
      await load();
      void pollWhileScoring();
    } catch (e) {
      setError(String(e));
      setBusy(null);
    }
  }

  async function onRescore() {
    if (!id) return;
    setBusy("rescore");
    setError(null);
    setStatusMessage(null);
    try {
      const resp = await rescoreSource(Number(id));
      setStatusMessage(resp.status_message);
      await load();
      void pollWhileScoring();
    } catch (e) {
      setError(String(e));
      setBusy(null);
    }
  }

  async function onPasteTranscript() {
    if (!id || !transcriptDraft.trim()) return;
    setBusy("transcript");
    setError(null);
    setStatusMessage(null);
    try {
      const resp = await pasteTranscript(Number(id), transcriptDraft.trim());
      setStatusMessage(resp.status_message);
      setTranscriptDraft("");
      await load();
      void pollWhileScoring();
    } catch (e) {
      setError(String(e));
      setBusy(null);
    }
  }

  if (!detail && !error) return <p>Loading…</p>;

  const { source, scores, note_path: notePath } = detail ?? {
    source: null,
    scores: null,
    note_path: null,
  };
  const framing = scores?.framing ?? {};
  const missingText = !source?.normalized_text;
  const isYoutube = source?.source_type === "youtube";
  const isCaptured = source?.status === "captured";
  const headline = displayTitle(detail);
  const scoreAxes = scores ? scoreRadarAxes(scores) : null;
  const themeAxes =
    scores?.theme_breakdown && Object.keys(scores.theme_breakdown).length > 0
      ? themeRadarAxes(scores.theme_breakdown)
      : null;

  return (
    <AppShell back={{ to: "/", label: "← Queue" }}>
      {source && (
        <header className="source-detail__hero">
          <div className="source-detail__hero-row">
            <div className="source-detail__hero-main">
              <div className="source-detail__title-row">
                <h1 className="source-detail__title">{headline}</h1>
                {isCaptured && <span className="badge badge--high">Captured</span>}
              </div>
              {source.title && source.title !== headline && (
                <p className="source-detail__raw-title">Original: {source.title}</p>
              )}
              <p className="meta source-detail__meta">
                {source.source_type} · {source.genre} ·{" "}
                {source.status === "scoring"
                  ? "scoring…"
                  : `priority ${priorityScore(scores).toFixed(1)}`}
                {scores?.confidence ? ` · ${scores.confidence} confidence` : ""}
              </p>
              {source.url && (
                <a className="source-detail__url" href={source.url} target="_blank" rel="noreferrer">
                  {source.url}
                </a>
              )}
              {notePath && (
                <p className="source-detail__vault-path">
                  Vault note: <code className="inline-code">{notePath}</code>
                </p>
              )}
            </div>
            <div className="source-detail__toolbar">
              <button
                type="button"
                className="btn btn--primary"
                onClick={() => navigate(`/sources/${source.id}/capture`)}
                disabled={isCaptured}
              >
                {isCaptured ? "Captured" : "Capture"}
              </button>
              <button type="button" className="btn" onClick={onRefetch} disabled={busy !== null}>
                {busy === "refetch" ? "Re-fetching…" : "Re-fetch"}
              </button>
              <button
                type="button"
                className="btn"
                onClick={onRescore}
                disabled={busy !== null || missingText}
              >
                {busy === "rescore" ? "Re-scoring…" : "Re-score"}
              </button>
            </div>
          </div>

          {missingText && isYoutube && (
            <section className="transcript-panel">
              <h2>YouTube transcript unavailable</h2>
              <p className="meta">
                YouTube blocked automatic caption fetch from this network. Meridian scored
                from the video title only (low confidence). Paste a transcript below for a
                proper radar pass.
              </p>
              <textarea
                value={transcriptDraft}
                onChange={(e) => setTranscriptDraft(e.target.value)}
                placeholder="Paste transcript text here…"
                rows={8}
              />
              <div className="actions">
                <button
                  onClick={onPasteTranscript}
                  disabled={busy !== null || !transcriptDraft.trim()}
                >
                  {busy === "transcript" ? "Saving…" : "Save transcript & re-score"}
                </button>
              </div>
            </section>
          )}
          {missingText && !isYoutube && (
            <p className="error">
              No article text stored — radar was guessing. Re-fetch to pull the body and score properly.
            </p>
          )}
        </header>
      )}

      {scores && (framing.point || framing.matters_for_goals) && (
        <section className="executive-panel panel">
          <h2 className="section-title">Executive summary</h2>
          {framing.point && <p className="executive-panel__summary">{framing.point}</p>}
          {framing.matters_for_goals && (
            <article className="executive-panel__goals">
              <h3>How this ties to your goals</h3>
              <p>{framing.matters_for_goals}</p>
            </article>
          )}
        </section>
      )}

      {scores && scoreAxes && (
        <section className="radar-panel">
          <div className="radar-panel__header">
            <h2>Radar</h2>
            <p className="meta">Priority axes for this source against your goals.</p>
          </div>
          <div className="radar-panel__grid">
            <div className="radar-panel__chart">
              <RadarChart labels={scoreAxes.labels} values={scoreAxes.values} size={220} />
            </div>
            <ul className="radar-panel__legend">
              <li><span>Relevance</span><strong>{scores.relevance}</strong></li>
              <li><span>Urgency</span><strong>{scores.urgency0}</strong></li>
              <li><span>Depth</span><strong>{scores.depth_required}</strong></li>
              <li><span>Curiosity</span><strong>{scores.curiosity}</strong></li>
              <li><span>Effort</span><strong>{scores.effort}h</strong></li>
            </ul>
          </div>
        </section>
      )}

      {scores && themeAxes && (
        <section className="radar-panel radar-panel--themes">
          <div className="radar-panel__header">
            <h2>Goal themes</h2>
            <p className="meta">How this source maps to themes in goals.md.</p>
          </div>
          <div className="radar-panel__grid">
            <div className="radar-panel__chart">
              <RadarChart
                labels={themeAxes.labels}
                values={themeAxes.values}
                color="var(--color-radar-theme)"
                size={200}
              />
            </div>
            <ul className="theme-list">
              {themeAxes.fullLabels.map((theme, index) => (
                <li key={theme}>
                  <span>{theme}</span>
                  <strong>{themeAxes.values[index]}</strong>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {scores?.reading_plan && scores.reading_plan.length > 0 && (
        <section className="panel">
          <h2 className="section-title">Reading plan</h2>
          <ReadingPlan steps={scores.reading_plan} />
        </section>
      )}

      {statusMessage && <p className="meta">{statusMessage}</p>}
      {error && <p className="error">{error}</p>}
    </AppShell>
  );
}

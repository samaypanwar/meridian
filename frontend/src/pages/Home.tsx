import { useCallback, useEffect, useRef, useState } from "react";
import AppShell from "../components/AppShell";
import CycleStrip from "../components/CycleStrip";
import SourceCard from "../components/SourceCard";
import {
  addSource,
  getGoals,
  getQueue,
  getSource,
  sleep,
  type AddSourceResponse,
  type SourceDetail,
} from "../api";

interface PendingAdd {
  id: number;
  ref: string;
  title: string | null;
  scoringModel: string;
  statusMessage: string;
  phase: "scoring" | "ready" | "failed";
  error?: string;
}

type QueueView = "list" | "grid";
type PageSize = 10 | 20 | 30;

const PAGE_SIZES: PageSize[] = [10, 20, 30];

export default function Home() {
  const [ref, setRef] = useState("");
  const [active, setActive] = useState<SourceDetail[]>([]);
  const [backlog, setBacklog] = useState<SourceDetail[]>([]);
  const [showBacklog, setShowBacklog] = useState(false);
  const [pendingAdds, setPendingAdds] = useState<PendingAdd[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cycleCaptures, setCycleCaptures] = useState(0);
  const [cyclePassRate, setCyclePassRate] = useState(0);
  const [queueView, setQueueView] = useState<QueueView>("grid");
  const [pageSize, setPageSize] = useState<PageSize>(10);
  const [page, setPage] = useState(0);
  const pollTimers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    getGoals()
      .then((data) => {
        const ind = data.indicators as { captures_this_cycle?: number; review_pass_rate?: number };
        setCycleCaptures(ind.captures_this_cycle ?? 0);
        setCyclePassRate(ind.review_pass_rate ?? 0);
      })
      .catch(() => undefined);
  }, []);

  const refresh = useCallback(async () => {
    const data = await getQueue();
    setActive(data.active);
    setBacklog(data.backlog ?? []);
    setPendingAdds((current) => {
      const serverPendingIds = new Set(data.pending.map((item) => item.source.id));
      const merged = current.filter(
        (item) => item.phase === "scoring" || serverPendingIds.has(item.id),
      );
      for (const item of data.pending) {
        if (!merged.some((entry) => entry.id === item.source.id)) {
          merged.push({
            id: item.source.id,
            ref: item.source.url ?? item.source.title ?? "Source",
            title: item.source.title,
            scoringModel: "unknown",
            statusMessage: "Radar pass running against goals.md…",
            phase: "scoring",
          });
        }
      }
      return merged;
    });
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
    return () => {
      for (const timer of pollTimers.current.values()) {
        clearTimeout(timer);
      }
    };
  }, [refresh]);

  async function pollUntilScored(sourceId: number) {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      await sleep(2000);
      try {
        const detail = await getSource(sourceId);
        if (detail.scores) {
          setPendingAdds((current) =>
            current.map((item) =>
              item.id === sourceId ? { ...item, phase: "ready" as const } : item,
            ),
          );
          await refresh();
          window.setTimeout(() => {
            setPendingAdds((current) => current.filter((item) => item.id !== sourceId));
          }, 2500);
          return;
        }
        if (detail.source.status === "revisit" && !detail.scores) {
          setPendingAdds((current) =>
            current.map((item) =>
              item.id === sourceId
                ? {
                  ...item,
                  phase: "failed" as const,
                  error: "Radar pass failed. Source flagged for revisit.",
                }
                : item,
            ),
          );
          return;
        }
      } catch (pollError) {
        setPendingAdds((current) =>
          current.map((item) =>
            item.id === sourceId
              ? { ...item, phase: "failed" as const, error: String(pollError) }
              : item,
          ),
        );
        return;
      }
    }
    setPendingAdds((current) =>
      current.map((item) =>
        item.id === sourceId
          ? {
            ...item,
            phase: "failed" as const,
            error: "Scoring is taking longer than expected. It may still finish in the background.",
          }
          : item,
      ),
    );
  }

  function trackPendingAdd(result: AddSourceResponse, submittedRef: string) {
    const entry: PendingAdd = {
      id: result.source.id,
      ref: submittedRef,
      title: result.source.title,
      scoringModel: result.scoring_model,
      statusMessage: result.status_message,
      phase: "scoring",
    };
    setPendingAdds((current) => [entry, ...current.filter((item) => item.id !== entry.id)]);
    void pollUntilScored(entry.id);
  }

  useEffect(() => {
    setPage(0);
  }, [pageSize, queueView, active.length]);

  const pageCount = Math.max(1, Math.ceil(active.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const pageStart = safePage * pageSize;
  const visibleActive = active.slice(pageStart, pageStart + pageSize);
  const pageEnd = Math.min(pageStart + pageSize, active.length);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    const submittedRef = ref.trim();
    if (!submittedRef) return;
    setRef("");
    setError(null);
    try {
      const result = await addSource(submittedRef);
      trackPendingAdd(result, submittedRef);
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <AppShell>
      <section className="hero-add">
        <h1>What should get your attention?</h1>
        <p className="hero-add__sub">Paste a link</p>
        <form className="add-bar" onSubmit={onAdd}>
          <input
            value={ref}
            onChange={(e) => setRef(e.target.value)}
            placeholder="URL, PDF path, or YouTube link"
          />
          <button type="submit" className="btn btn--primary">
            Add source
          </button>
        </form>
        {error && <p className="error">{error}</p>}
        <CycleStrip captures={cycleCaptures} passRate={cyclePassRate} />
      </section>

      {pendingAdds.length > 0 && (
        <section className="pending-section">
          <h2 className="section-title">In progress</h2>
          <ul className="pending-cards">
            {pendingAdds.map((item) => (
              <li key={item.id} className={`pending-card pending-card--${item.phase}`}>
                <div className="pending-card__header">
                  <strong>{item.title ?? item.ref}</strong>
                  {item.phase === "scoring" && <span className="spinner" aria-hidden="true" />}
                </div>
                <p className="pending-card__url">{item.ref}</p>
                <p className="pending-card__message">
                  {item.phase === "scoring" && item.statusMessage}
                  {item.phase === "ready" && "Scored and added to your queue."}
                  {item.phase === "failed" && (item.error ?? "Scoring failed.")}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="queue-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Active queue</h2>
            <span className="section-caption">
              {active.length} sources · sorted by priority
            </span>
          </div>
          <div className="queue-controls">
            <div className="queue-controls__group" role="group" aria-label="Queue layout">
              <button
                type="button"
                className={`queue-controls__btn${queueView === "grid" ? " queue-controls__btn--active" : ""}`}
                onClick={() => setQueueView("grid")}
              >
                Grid
              </button>
              <button
                type="button"
                className={`queue-controls__btn${queueView === "list" ? " queue-controls__btn--active" : ""}`}
                onClick={() => setQueueView("list")}
              >
                List
              </button>
            </div>
            <label className="queue-controls__size">
              <span className="queue-controls__size-label">Per page</span>
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value) as PageSize)}
              >
                {PAGE_SIZES.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        {active.length === 0 ? (
          <p className="empty-state">Queue is empty. Add a source above.</p>
        ) : (
          <>
            <ul
              className={`source-card-grid${queueView === "grid" ? " source-card-grid--two-col" : " source-card-grid--list"
                }`}
            >
              {visibleActive.map((item, index) => (
                <li
                  key={item.source.id}
                  className={pageStart + index === 0 ? "source-card-grid__hero" : undefined}
                >
                  <SourceCard item={item} layout={queueView} />
                </li>
              ))}
            </ul>
            {active.length > pageSize && (
              <div className="queue-pagination">
                <span className="queue-pagination__summary">
                  Showing {pageStart + 1}–{pageEnd} of {active.length}
                </span>
                <div className="queue-pagination__actions">
                  <button
                    type="button"
                    className="btn"
                    disabled={safePage === 0}
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                  >
                    Previous
                  </button>
                  <span className="queue-pagination__page">
                    Page {safePage + 1} of {pageCount}
                  </span>
                  <button
                    type="button"
                    className="btn"
                    disabled={safePage >= pageCount - 1}
                    onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {backlog.length > 0 && (
        <section className="backlog-section">
          <button
            type="button"
            className="backlog-toggle"
            onClick={() => setShowBacklog((v) => !v)}
          >
            {showBacklog ? "Hide" : "Show"} backlog ({backlog.length})
          </button>
          {showBacklog && (
            <ul className="source-card-grid source-card-grid--compact">
              {backlog.map((item) => (
                <li key={item.source.id}>
                  <SourceCard item={item} compact />
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </AppShell>
  );
}

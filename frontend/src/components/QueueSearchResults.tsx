import SourceCard from "./SourceCard";
import type { QueueMode, SourceDetail } from "../api";

interface QueueSearchResultsProps {
  query: string;
  queueItems: SourceDetail[];
  captureText: string | null;
  citations: string[];
  rankMode: QueueMode;
  loading?: boolean;
  error?: string | null;
}

export default function QueueSearchResults({
  query,
  queueItems,
  captureText,
  citations,
  rankMode,
  loading = false,
  error = null,
}: QueueSearchResultsProps) {
  if (!query.trim()) return null;

  return (
    <section className="queue-search-results panel">
      <header className="queue-search-results__header">
        <h2 className="section-title section-title--small">Search results</h2>
        <p className="section-caption">
          {loading
            ? "Searching…"
            : `Results for “${query}”`}
        </p>
      </header>

      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <>
          <div className="queue-search-results__section">
            <h3 className="section-title section-title--small">In your queue</h3>
            {queueItems.length === 0 ? (
              <p className="empty-state">No queue sources match.</p>
            ) : (
              <ul className="source-card-grid source-card-grid--list">
                {queueItems.map((item) => (
                  <li key={item.source.id}>
                    <SourceCard item={item} layout="list" rankMode={rankMode} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {(captureText || citations.length > 0) && (
            <div className="queue-search-results__section">
              <h3 className="section-title section-title--small">Already captured</h3>
              {captureText && <div className="kb-answer">{captureText}</div>}
              {citations.length > 0 && (
                <ul className="citation-list">
                  {citations.map((citation) => (
                    <li key={citation}>{citation}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}

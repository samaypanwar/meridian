import { useState } from "react";
import AppShell from "../components/AppShell";
import { kbQuery } from "../api";

export default function KnowledgePage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setError(null);
    try {
      const result = await kbQuery(q);
      setAnswer(result.text);
      setCitations(result.citations ?? []);
    } catch (err) {
      setError(String(err));
      setAnswer(null);
      setCitations([]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Knowledge">
      <header className="knowledge-hero">
        <h1>What do I believe?</h1>
        <p className="section-caption">
          Query your vault extractions — grounded answers with citations.
        </p>
      </header>

      <form className="add-bar" onSubmit={onSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What do I believe about policy gradient variance?"
        />
        <button type="submit" className="btn btn--primary" disabled={busy}>
          {busy ? "Searching…" : "Ask"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {answer && (
        <section className="panel">
          <h2 className="section-title">Answer</h2>
          <div className="kb-answer">{answer}</div>
          {citations.length > 0 && (
            <>
              <h3 className="section-title section-title--small">Citations</h3>
              <ul className="citation-list">
                {citations.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </AppShell>
  );
}

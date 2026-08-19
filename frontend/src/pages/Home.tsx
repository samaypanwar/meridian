import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { addSource, getQueue, priorityScore, type SourceDetail } from "./api";

export default function Home() {
  const [ref, setRef] = useState("");
  const [items, setItems] = useState<SourceDetail[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const data = await getQueue();
    setItems(data.active);
  }

  useEffect(() => {
    refresh().catch((e) => setError(String(e)));
  }, []);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!ref.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await addSource(ref.trim());
      setRef("");
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <header>
        <h1>Meridian</h1>
        <nav>
          <Link to="/goals">Goals</Link>
          <Link to="/review">Review</Link>
        </nav>
      </header>

      <form className="add-bar" onSubmit={onAdd}>
        <input
          value={ref}
          onChange={(e) => setRef(e.target.value)}
          placeholder="Paste URL, PDF path, or YouTube link"
        />
        <button disabled={loading}>{loading ? "Adding…" : "Add"}</button>
      </form>
      {error && <p className="error">{error}</p>}

      <section>
        <h2>Active queue</h2>
        <ul className="queue">
          {items.map((item) => (
            <li key={item.source.id}>
              <Link to={`/sources/${item.source.id}`}>
                <strong>{item.source.title ?? item.source.url}</strong>
              </Link>
              <span className="meta">
                {item.source.genre} · priority {priorityScore(item.scores).toFixed(1)}
              </span>
              <span className="radar">
                R{item.scores?.relevance ?? "-"} U{item.scores?.urgency0 ?? "-"} E
                {item.scores?.effort ?? "-"}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

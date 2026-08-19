import { Link, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { getSource, priorityScore, type SourceDetail } from "../api";

export default function SourceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SourceDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getSource(Number(id))
      .then(setDetail)
      .catch((e) => setError(String(e)));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!detail) return <p>Loading…</p>;

  const { source, scores } = detail;
  const framing = scores?.framing ?? {};

  return (
    <main className="page">
      <Link to="/">← Queue</Link>
      <h1>{source.title ?? source.url}</h1>
      <p className="meta">
        {source.source_type} · {source.genre} · priority {priorityScore(scores).toFixed(1)}
      </p>

      {scores && (
        <section className="radar-panel">
          <h2>Radar</h2>
          <ul>
            <li>Relevance: {scores.relevance}</li>
            <li>Urgency: {scores.urgency0}</li>
            <li>Effort: {scores.effort}h</li>
            <li>Depth: {scores.depth_required}</li>
            <li>Curiosity: {scores.curiosity}</li>
          </ul>
          {scores.theme_breakdown && (
            <p>Themes: {Object.keys(scores.theme_breakdown).join(", ")}</p>
          )}
        </section>
      )}

      <section>
        <h2>Framing</h2>
        <p><strong>Point:</strong> {framing.point}</p>
        <p><strong>Matters for goals:</strong> {framing.matters_for_goals}</p>
        <p><strong>Where to focus:</strong> {framing.where_to_focus}</p>
      </section>

      {scores?.reading_plan && scores.reading_plan.length > 0 && (
        <section>
          <h2>Reading plan</h2>
          <pre>{JSON.stringify(scores.reading_plan, null, 2)}</pre>
        </section>
      )}

      <div className="actions">
        <button onClick={() => navigate(`/sources/${source.id}/capture`)}>Capture</button>
      </div>
    </main>
  );
}

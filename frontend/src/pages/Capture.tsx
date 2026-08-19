import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { captureApprove, capturePreview } from "../api";

export default function CapturePage() {
  const { id } = useParams();
  const [reflection, setReflection] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [shallow, setShallow] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onPreview() {
    if (!id) return;
    setError(null);
    try {
      const result = await capturePreview(Number(id), reflection);
      setShallow(result.shallow);
      setPreview(result.preview);
    } catch (e) {
      setError(String(e));
    }
  }

  async function onSave() {
    if (!id || !preview) return;
    try {
      const result = await captureApprove(Number(id), preview);
      setSaved(`${result.status} → ${result.note_path}`);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <main className="page">
      <Link to={`/sources/${id}`}>← Source</Link>
      <h1>Capture</h1>
      <textarea
        value={reflection}
        onChange={(e) => setReflection(e.target.value)}
        placeholder="What did you take from this source?"
        rows={6}
      />
      <div className="actions">
        <button onClick={onPreview}>Draft note</button>
        {preview && !shallow && <button onClick={onSave}>Save to vault</button>}
      </div>
      {shallow && <p className="error">Nothing stuck — flagged for revisit.</p>}
      {preview && <pre className="preview">{preview}</pre>}
      {saved && <p>{saved}</p>}
      {error && <p className="error">{error}</p>}
    </main>
  );
}

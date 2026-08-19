import { useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import AppShell from "../components/AppShell";
import StepIndicator from "../components/StepIndicator";
import { captureApprove, capturePreview, getSource } from "../api";

export default function CapturePage() {
  const { id } = useParams();
  const [reflection, setReflection] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [shallow, setShallow] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [objective, setObjective] = useState<string | null>(null);
  const [title, setTitle] = useState<string | null>(null);
  const [busy, setBusy] = useState<"preview" | "save" | null>(null);

  const step = useMemo((): 0 | 1 | 2 => {
    if (saved) return 2;
    if (preview && !shallow) return 1;
    return 0;
  }, [preview, shallow, saved]);

  useEffect(() => {
    if (!id) return;
    getSource(Number(id))
      .then((detail) => {
        setTitle(detail.scores?.framing?.display_title ?? detail.source.title);
        setObjective(detail.scores?.framing?.matters_for_goals ?? null);
      })
      .catch(console.error);
  }, [id]);

  async function onPreview() {
    if (!id) return;
    setBusy("preview");
    setError(null);
    setSaved(null);
    try {
      const result = await capturePreview(Number(id), reflection);
      setShallow(result.shallow);
      setPreview(result.preview);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function onSave() {
    if (!id || !preview) return;
    setBusy("save");
    setError(null);
    try {
      const result = await captureApprove(Number(id), preview);
      setSaved(`${result.status} → ${result.note_path}`);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <AppShell back={{ to: `/sources/${id}`, label: "← Back to source" }} narrow>
      <header className="capture-hero">
        <StepIndicator active={step} />
        <h1>{title ?? "Capture"}</h1>
        {objective && (
          <article className="framing-card framing-card--primary">
            <h3>Objective for this source</h3>
            <p>{objective}</p>
          </article>
        )}
      </header>

      <section className="panel">
        <h2 className="section-title">What did you take?</h2>
        <p className="section-caption">
          Write in your own words before drafting the vault note. Blank submission flags revisit.
        </p>
        <textarea
          className="capture-textarea"
          value={reflection}
          onChange={(e) => setReflection(e.target.value)}
          placeholder="The main claim I'm keeping, why it matters for my goals, and what I'd do differently…"
          rows={8}
        />
        <div className="actions">
          <button type="button" className="btn btn--primary" onClick={onPreview} disabled={busy !== null}>
            {busy === "preview" ? "Drafting…" : "Draft note"}
          </button>
          {preview && !shallow && (
            <button type="button" className="btn btn--primary" onClick={onSave} disabled={busy !== null}>
              {busy === "save" ? "Saving…" : "Save to vault"}
            </button>
          )}
        </div>
      </section>

      {shallow && (
        <p className="error panel">
          Nothing stuck — source flagged for revisit. Come back after another pass.
        </p>
      )}

      {preview && !shallow && (
        <section className="panel">
          <h2 className="section-title">Note preview</h2>
          <pre className="preview">{preview}</pre>
        </section>
      )}

      {saved && <p className="success panel">{saved}</p>}
      {error && <p className="error">{error}</p>}
    </AppShell>
  );
}

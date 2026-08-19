import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { getDueReviews, gradeReview, type ReviewItem } from "../api";

export default function ReviewPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [revealed, setRevealed] = useState(false);
  const [current, setCurrent] = useState<ReviewItem | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    const data = await getDueReviews();
    setReviews(data.reviews);
    setCurrent(data.reviews[0] ?? null);
    setRevealed(false);
    setMessage(null);
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function onGrade(grade: string) {
    if (!current) return;
    const result = await gradeReview(current.id, grade);
    setMessage(result.status === "revisit" ? "Missed twice — source flagged for revisit." : "Graded.");
    await load();
  }

  return (
    <AppShell focus>
      <div className="review-focus">
        <h1 className="review-focus__title">Spaced review</h1>
        <p className="section-caption">
          {reviews.length === 0
            ? "Nothing due right now."
            : `${reviews.length} card${reviews.length === 1 ? "" : "s"} due`}
        </p>

        {!current && <p className="empty-state">No reviews due. Capture notes to build your deck.</p>}

        {current && (
          <article className="review-card">
            <p className="review-card__label">Question</p>
            <p className="review-card__question">{current.question}</p>

            {!revealed ? (
              <button type="button" className="btn btn--primary btn--block" onClick={() => setRevealed(true)}>
                Reveal capture
              </button>
            ) : (
              <>
                <p className="review-card__label">From note</p>
                <p className="review-card__note">{current.note_path}</p>
                <div className="grade-actions">
                  <button type="button" className="grade grade--got" onClick={() => onGrade("got_it")}>
                    Got it
                  </button>
                  <button type="button" className="grade grade--partial" onClick={() => onGrade("partial")}>
                    Partial
                  </button>
                  <button type="button" className="grade grade--missed" onClick={() => onGrade("missed")}>
                    Missed
                  </button>
                </div>
              </>
            )}
          </article>
        )}

        {message && <p className="meta panel">{message}</p>}
        {reviews.length > 1 && current && (
          <p className="section-caption">{reviews.length - 1} more after this one</p>
        )}
      </div>
    </AppShell>
  );
}

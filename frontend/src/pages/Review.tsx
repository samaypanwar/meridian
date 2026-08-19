import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
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
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function onGrade(grade: string) {
    if (!current) return;
    const result = await gradeReview(current.id, grade);
    setMessage(result.status);
    await load();
  }

  return (
    <main className="page">
      <Link to="/">← Queue</Link>
      <h1>Review due</h1>
      {!current && <p>No reviews due.</p>}
      {current && (
        <section>
          <p className="question">{current.question}</p>
          {!revealed && <button onClick={() => setRevealed(true)}>Reveal capture</button>}
          {revealed && (
            <div className="actions">
              <button onClick={() => onGrade("got_it")}>Got it</button>
              <button onClick={() => onGrade("partial")}>Partial</button>
              <button onClick={() => onGrade("missed")}>Missed</button>
            </div>
          )}
        </section>
      )}
      {message && <p>{message}</p>}
      {reviews.length > 1 && <p>{reviews.length - 1} more in queue</p>}
    </main>
  );
}

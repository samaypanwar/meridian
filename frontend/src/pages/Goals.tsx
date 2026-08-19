import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getGoals } from "../api";

export default function GoalsPage() {
  const [goalsMd, setGoalsMd] = useState("");
  const [indicators, setIndicators] = useState<Record<string, unknown>>({});

  useEffect(() => {
    getGoals()
      .then((data) => {
        setGoalsMd(data.goals_md);
        setIndicators(data.indicators);
      })
      .catch(console.error);
  }, []);

  return (
    <main className="page">
      <Link to="/">← Queue</Link>
      <h1>Goals</h1>
      <section>
        <h2>Leading indicators</h2>
        <pre>{JSON.stringify(indicators, null, 2)}</pre>
      </section>
      <section>
        <h2>goals.md</h2>
        <pre className="goals-md">{goalsMd}</pre>
      </section>
    </main>
  );
}

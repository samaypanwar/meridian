import { useEffect, useMemo, useState } from "react";
import AppShell from "../components/AppShell";
import ProgressGauge from "../components/ProgressGauge";
import RadarChart from "../components/RadarChart";
import InlineMarkdown from "../components/InlineMarkdown";
import {
  defaultIndicatorTargets,
  parseGoalsMd,
  type ParsedGoals,
} from "../lib/goalsParse";
import { getGoals } from "../api";

interface Indicators {
  captures_by_theme?: Record<string, number>;
  review_pass_rate?: number;
  hours_by_theme?: Record<string, number>;
  captures_this_cycle?: number;
}

export default function GoalsPage() {
  const [goalsMd, setGoalsMd] = useState("");
  const [indicators, setIndicators] = useState<Indicators>({});
  const [expandedGoals, setExpandedGoals] = useState(false);

  useEffect(() => {
    getGoals()
      .then((data) => {
        setGoalsMd(data.goals_md);
        setIndicators(data.indicators as Indicators);
      })
      .catch(console.error);
  }, []);

  const parsed: ParsedGoals = useMemo(() => parseGoalsMd(goalsMd), [goalsMd]);
  const targets = defaultIndicatorTargets();

  const themeRadar = useMemo(() => {
    const captures = indicators.captures_by_theme ?? {};
    const labels = parsed.themes.map((t) => t.split("/").pop() ?? t);
    const values = parsed.themes.map((theme) => {
      const count = captures[theme] ?? 0;
      return Math.min(10, (count / Math.max(targets.capturesPerCycle, 1)) * 10);
    });
    return { labels, values, fullThemes: parsed.themes, captures };
  }, [parsed.themes, indicators.captures_by_theme, targets.capturesPerCycle]);

  return (
    <AppShell title="Goals">
      <header className="goals-hero">
        <p className="goals-hero__cycle">{parsed.cycle ?? "Current cycle"}</p>
        <h1>Learning north star</h1>
        {parsed.mission.map((line) => (
          <p key={line} className="goals-hero__mission">
            {line}
          </p>
        ))}
      </header>

      <section className="panel">
        <h2 className="section-title">Leading indicators</h2>
        <p className="section-caption">Progress inputs Meridian tracks this cycle</p>
        <div className="gauge-grid">
          <ProgressGauge
            label="Captures this cycle"
            value={indicators.captures_this_cycle ?? 0}
            target={targets.capturesPerCycle}
          />
          <ProgressGauge
            label="Review pass rate"
            value={indicators.review_pass_rate ?? 0}
            target={targets.reviewPassRate}
            format="percent"
          />
          <ProgressGauge
            label="RL hours / week"
            value={indicators.hours_by_theme?.["foundations/rl"] ?? 0}
            target={targets.hoursPerWeek}
            unit="h"
          />
        </div>
      </section>

      {parsed.themes.length > 0 && (
        <section className="panel">
          <h2 className="section-title">Theme activity</h2>
          <p className="section-caption">Captures per theme vs cycle target (proxy goals)</p>
          <div className="radar-panel__grid">
            <div className="radar-panel__chart">
              <RadarChart
                labels={themeRadar.labels}
                values={themeRadar.values}
                color="#59A14F"
                size={176}
              />
            </div>
            <ul className="theme-list">
              {themeRadar.fullThemes.map((theme, index) => (
                <li key={theme}>
                  <span>{theme}</span>
                  <strong>{themeRadar.captures[theme] ?? 0} captures</strong>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {parsed.objectives.length > 0 && (
        <section className="panel">
          <h2 className="section-title">Objectives</h2>
          <div className="objective-grid">
            {parsed.objectives.map((obj) => (
              <article key={obj.id} className="objective-card">
                <h3>{obj.title}</h3>
                <ul className="objective-list">
                  {obj.lines.map((line) => (
                    <li key={line}>
                      <InlineMarkdown text={line} />
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      )}

      {parsed.targetMix && Object.keys(parsed.targetMix).length > 0 && (
        <section className="panel">
          <h2 className="section-title">Target mix</h2>
          <div className="mix-bars">
            {Object.entries(parsed.targetMix).map(([lane, pct]) => (
              <div key={lane} className="mix-bar">
                <span className="mix-bar__label">{lane}</span>
                <div className="mix-bar__track">
                  <div className="mix-bar__fill" style={{ width: `${pct}%` }} />
                </div>
                <span className="mix-bar__pct">{pct}%</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel panel--muted">
        <button
          type="button"
          className="backlog-toggle"
          onClick={() => setExpandedGoals((v) => !v)}
        >
          {expandedGoals ? "Hide" : "Show"} raw goals.md
        </button>
        {expandedGoals && <pre className="goals-md">{goalsMd}</pre>}
      </section>
    </AppShell>
  );
}

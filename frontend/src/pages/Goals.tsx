import { useEffect, useMemo, useState } from "react";
import AppShell from "../components/AppShell";
import InlineMarkdown from "../components/InlineMarkdown";
import ProgressGauge from "../components/ProgressGauge";
import RadarChart from "../components/RadarChart";
import {
  defaultIndicatorTargets,
  parseGoalsMd,
  parseRationaleMd,
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
  const [rationaleMd, setRationaleMd] = useState("");
  const [indicators, setIndicators] = useState<Indicators>({});
  const [showRationale, setShowRationale] = useState(false);
  const [expandedGoals, setExpandedGoals] = useState(false);

  useEffect(() => {
    getGoals()
      .then((data) => {
        setGoalsMd(data.goals_md);
        setRationaleMd(data.goals_rationale_md ?? "");
        setIndicators(data.indicators as Indicators);
      })
      .catch(console.error);
  }, []);

  const parsed: ParsedGoals = useMemo(() => parseGoalsMd(goalsMd), [goalsMd]);
  const rationaleSections = useMemo(() => parseRationaleMd(rationaleMd), [rationaleMd]);
  const targets = defaultIndicatorTargets();

  const themeRadar = useMemo(() => {
    const captures = indicators.captures_by_theme ?? {};
    const labels = parsed.themes.map((t) => t.id.split("/").pop() ?? t.id);
    const values = parsed.themes.map((theme) => {
      const count = captures[theme.id] ?? 0;
      return Math.min(10, (count / Math.max(targets.capturesPerCycle, 1)) * 10);
    });
    return { labels, values, themes: parsed.themes, captures };
  }, [parsed.themes, indicators.captures_by_theme, targets.capturesPerCycle]);

  return (
    <AppShell title="Goals">
      <header className="goals-hero">
        <p className="goals-hero__cycle">{parsed.title ?? parsed.cycle ?? "Current cycle"}</p>
        <h1>Learning north star</h1>
        {parsed.mission.map((line) => (
          <p key={line} className="goals-hero__mission">
            {line}
          </p>
        ))}
        {rationaleMd && (
          <button
            type="button"
            className="goals-rationale-link"
            onClick={() => setShowRationale((v) => !v)}
          >
            {showRationale ? "Hide" : "Why these goals?"}
            <span className="goals-rationale-link__hint"> — motivation & tradeoffs</span>
          </button>
        )}
      </header>

      {showRationale && rationaleSections.length > 0 && (
        <section className="panel goals-rationale-panel">
          <h2 className="section-title">Goals rationale</h2>
          <p className="section-caption">
            Not scored by Meridian — why each objective exists and what this cycle is not.
          </p>
          <div className="goals-rationale-sections">
            {rationaleSections.map((section) => (
              <article key={section.title} className="goals-rationale-section">
                <h3>{section.title}</h3>
                <div className="goals-rationale-section__body">
                  {section.body.split("\n\n").map((para) => (
                    <p key={para.slice(0, 40)}>{para}</p>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

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
          <h2 className="section-title">Themes</h2>
          <p className="section-caption">What Meridian tags sources against</p>
          <ul className="theme-card-list">
            {parsed.themes.map((theme) => (
              <li key={theme.id} className="theme-card">
                <code className="theme-card__id">{theme.id}</code>
                {theme.description && <p className="theme-card__desc">{theme.description}</p>}
                <span className="theme-card__captures">
                  {themeRadar.captures[theme.id] ?? 0} captures
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {parsed.themes.length > 0 && (
        <section className="panel">
          <h2 className="section-title">Theme activity</h2>
          <p className="section-caption">Capture volume vs cycle target (proxy)</p>
          <div className="radar-panel__grid">
            <div className="radar-panel__chart">
              <RadarChart
                labels={themeRadar.labels}
                values={themeRadar.values}
                color="var(--color-radar-theme)"
                size={176}
              />
            </div>
            <ul className="theme-list">
              {themeRadar.themes.map((theme, index) => (
                <li key={theme.id}>
                  <span>{theme.id}</span>
                  <strong>{themeRadar.captures[theme.id] ?? 0}</strong>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {parsed.objectives.length > 0 && (
        <section className="panel">
          <h2 className="section-title">Objectives</h2>
          <p className="section-caption">{parsed.objectives.length} parallel threads this cycle</p>
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

      {parsed.curiosity.length > 0 && (
        <section className="panel panel--muted">
          <h2 className="section-title">Curiosity</h2>
          <p className="section-caption">Explore mode — no proof required</p>
          <ul className="curiosity-list">
            {parsed.curiosity.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
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

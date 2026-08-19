import { Link } from "react-router-dom";
import MiniRadar from "./MiniRadar";
import ThemeChips from "./ThemeChips";
import { displayTitle, priorityScore, type QueueMode, type SourceDetail } from "../api";

export type SourceCardLayout = "list" | "grid";

function confidenceClass(confidence: string | null | undefined): string {
  if (confidence === "high") return "badge badge--high";
  if (confidence === "medium") return "badge badge--medium";
  return "badge badge--low";
}

export default function SourceCard({
  item,
  compact = false,
  layout = "list",
  rankMode = "goals",
}: {
  item: SourceDetail;
  compact?: boolean;
  layout?: SourceCardLayout;
  rankMode?: QueueMode;
}) {
  const { source, scores } = item;
  const priority = priorityScore(scores);
  const curiosity = scores?.curiosity ?? 0;
  const rankLabel =
    rankMode === "curiosity" ? curiosity.toFixed(1) : priority.toFixed(1);
  const rankClass =
    rankMode === "curiosity" ? "badge badge--curiosity" : "badge badge--priority";
  const radarSize = layout === "grid" ? 128 : 148;

  return (
    <article
      className={`source-card${compact ? " source-card--compact" : ""}${layout === "grid" ? " source-card--grid" : " source-card--list"
        }`}
    >
      <Link to={`/sources/${source.id}`} className="source-card__link">
        <div className="source-card__top">
          <div className="source-card__headline">
            <h3>{displayTitle(item)}</h3>
            <div className="source-card__badges">
              <span className={rankClass} title={rankMode === "curiosity" ? "Curiosity" : "Priority"}>
                {rankLabel}
              </span>
              {scores?.confidence && (
                <span className={confidenceClass(scores.confidence)}>{scores.confidence}</span>
              )}
            </div>
          </div>
          {!compact && scores && (
            <div className="source-card__radar">
              <MiniRadar scores={scores} size={radarSize} />
            </div>
          )}
        </div>
        <p className="source-card__meta">
          {source.genre} · {source.source_type}
          {source.status === "scoring" ? " · scoring…" : ""}
        </p>
        {scores?.framing?.point && !compact && (
          <p className="source-card__hook">{scores.framing.point}</p>
        )}
        <ThemeChips themes={scores?.theme_breakdown ?? null} />
      </Link>
    </article>
  );
}

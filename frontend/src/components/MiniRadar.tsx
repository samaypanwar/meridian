import RadarChart, { accessibilityScore } from "./RadarChart";
import type { Scores } from "../api";

export default function MiniRadar({ scores, size = 108 }: { scores: Scores; size?: number }) {
  return (
    <RadarChart
      size={size}
      labels={["R", "U", "D", "C", "A"]}
      values={[
        scores.relevance ?? 0,
        scores.urgency0 ?? 0,
        scores.depth_required ?? 0,
        scores.curiosity ?? 0,
        accessibilityScore(scores.effort),
      ]}
      fillOpacity={0.18}
    />
  );
}

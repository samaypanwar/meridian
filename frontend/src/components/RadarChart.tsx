const DEFAULT_SIZE = 192;
const LABEL_OFFSET = 14;
const INNER_PAD = 22;
const VIEW_MARGIN = 30;

interface RadarChartProps {
  labels: string[];
  values: number[];
  max?: number;
  size?: number;
  color?: string;
  fillOpacity?: number;
}

function polarPoint(
  center: number,
  radius: number,
  angleRad: number,
): [number, number] {
  return [
    center + radius * Math.sin(angleRad),
    center - radius * Math.cos(angleRad),
  ];
}

export default function RadarChart({
  labels,
  values,
  max = 10,
  size = DEFAULT_SIZE,
  color = "var(--color-radar)",
  fillOpacity = 0.22,
}: RadarChartProps) {
  const count = labels.length;
  if (count === 0) return null;

  const compact = size < 160;
  const innerPad = compact ? Math.max(10, Math.round(size * 0.1)) : INNER_PAD;
  const viewMargin = compact ? Math.max(12, Math.round(size * 0.12)) : VIEW_MARGIN;
  const labelOffset = compact ? 10 : LABEL_OFFSET;

  const center = size / 2;
  const outer = center - innerPad;
  const viewSize = size + viewMargin * 2;
  const rings = [0.25, 0.5, 0.75, 1];

  const angleFor = (index: number) => (Math.PI * 2 * index) / count;

  const valuePoints = values.map((value, index) => {
    const clamped = Math.max(0, Math.min(max, value));
    const radius = (clamped / max) * outer;
    return polarPoint(center, radius, angleFor(index));
  });

  const polygon = valuePoints.map(([x, y]) => `${x},${y}`).join(" ");

  return (
    <svg
      className="radar-chart"
      width={size}
      height={size}
      viewBox={`${-viewMargin} ${-viewMargin} ${viewSize} ${viewSize}`}
      role="img"
      aria-label="Radar chart"
    >
      {rings.map((ring) => {
        const ringPoints = labels
          .map((_, index) => {
            const [x, y] = polarPoint(center, outer * ring, angleFor(index));
            return `${x},${y}`;
          })
          .join(" ");
        return (
          <polygon
            key={ring}
            points={ringPoints}
            fill="none"
            stroke="var(--color-radar-grid)"
            strokeWidth={1}
          />
        );
      })}

      {labels.map((label, index) => {
        const [x, y] = polarPoint(center, outer, angleFor(index));
        const [lx, ly] = polarPoint(center, outer + labelOffset, angleFor(index));
        return (
          <g key={label}>
            <line x1={center} y1={center} x2={x} y2={y} stroke="var(--color-radar-axis)" strokeWidth={1} />
            <text
              x={lx}
              y={ly}
              textAnchor="middle"
              dominantBaseline="middle"
              className="radar-chart__label"
            >
              {label}
            </text>
          </g>
        );
      })}

      <polygon
        points={polygon}
        fill={color}
        fillOpacity={fillOpacity}
        stroke={color}
        strokeWidth={2}
      />

      {valuePoints.map(([x, y], index) => (
        <circle key={labels[index]} cx={x} cy={y} r={3.5} fill={color} />
      ))}
    </svg>
  );
}

export function accessibilityScore(effortHours: number | null | undefined): number {
  if (!effortHours || effortHours <= 0) return 0;
  return Math.max(0, Math.min(10, 10 - effortHours));
}

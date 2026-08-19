export default function ProgressGauge({
  label,
  value,
  target,
  unit,
  format = "number",
}: {
  label: string;
  value: number;
  target: number;
  unit?: string;
  format?: "number" | "percent";
}) {
  const pct = target > 0 ? Math.min(100, (value / target) * 100) : 0;
  const display =
    format === "percent"
      ? `${Math.round(value * 100)}%`
      : `${value}${unit ? ` ${unit}` : ""}`;

  return (
    <article className="gauge">
      <div className="gauge__header">
        <span className="gauge__label">{label}</span>
        <span className="gauge__value">
          {display}
          <span className="gauge__target">
            {" "}
            / {format === "percent" ? `${Math.round(target * 100)}%` : `${target}${unit ? ` ${unit}` : ""}`}
          </span>
        </span>
      </div>
      <div className="gauge__track">
        <div className="gauge__fill" style={{ width: `${pct}%` }} />
      </div>
    </article>
  );
}

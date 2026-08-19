type LogoVariant = "radar" | "arc" | "monogram";

export default function Logo({
  variant = "radar",
  size = 32,
}: {
  variant?: LogoVariant;
  size?: number;
}) {
  if (variant === "monogram") {
    return (
      <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden>
        <rect x={1} y={1} width={38} height={38} rx={10} fill="var(--color-accent)" />
        <text x={20} y={26} textAnchor="middle" fill="#fff" fontSize={18} fontWeight={600}>
          M
        </text>
      </svg>
    );
  }
  if (variant === "arc") {
    return (
      <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden>
        <path
          d="M8 28 A16 16 0 0 1 32 28"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={2.5}
        />
        <circle cx={20} cy={14} r={3} fill="var(--color-accent)" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden>
      <polygon
        points="20,6 34,16 30,32 10,32 6,16"
        fill="var(--color-accent)"
        fillOpacity={0.18}
        stroke="var(--color-accent)"
        strokeWidth={2}
      />
      <circle cx={20} cy={20} r={2.5} fill="var(--color-accent)" />
    </svg>
  );
}

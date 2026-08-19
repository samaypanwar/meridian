const COLORS = ["#4E79A7", "#59A14F", "#F28E2B", "#B07AA1", "#76B7B2", "#E15759"];

export default function ThemeChips({
  themes,
}: {
  themes: Record<string, number> | null | undefined;
}) {
  const entries = themes
    ? Object.entries(themes).sort((a, b) => b[1] - a[1])
    : [];

  if (entries.length === 0) return null;

  return (
    <ul className="theme-chips">
      {entries.map(([theme, value], index) => (
        <li
          key={theme}
          className="theme-chip"
          style={{ borderColor: COLORS[index % COLORS.length] }}
        >
          <span className="theme-chip__name">{theme.split("/").pop() ?? theme}</span>
          <span className="theme-chip__score">{value.toFixed(0)}</span>
        </li>
      ))}
    </ul>
  );
}

import { useTheme } from "../hooks/useTheme";

export default function ThemeToggle() {
  const { resolved, toggle } = useTheme();
  const isDark = resolved === "ink";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? (
        <svg width={18} height={18} viewBox="0 0 24 24" aria-hidden>
          <circle cx={12} cy={12} r={4} fill="currentColor" />
          <g stroke="currentColor" strokeWidth={2} fill="none">
            <line x1={12} y1={2} x2={12} y2={5} />
            <line x1={12} y1={19} x2={12} y2={22} />
            <line x1={2} y1={12} x2={5} y2={12} />
            <line x1={19} y1={12} x2={22} y2={12} />
            <line x1={4.2} y1={4.2} x2={6.3} y2={6.3} />
            <line x1={17.7} y1={17.7} x2={19.8} y2={19.8} />
            <line x1={4.2} y1={19.8} x2={6.3} y2={17.7} />
            <line x1={17.7} y1={6.3} x2={19.8} y2={4.2} />
          </g>
        </svg>
      ) : (
        <svg width={18} height={18} viewBox="0 0 24 24" aria-hidden>
          <path
            d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5Z"
            fill="currentColor"
          />
        </svg>
      )}
    </button>
  );
}

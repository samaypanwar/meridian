import { Link, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import Logo from "./Logo";
import ThemeToggle from "./ThemeToggle";

const NAV = [
  { to: "/", label: "Queue" },
  { to: "/goals", label: "Goals" },
  { to: "/review", label: "Review" },
  { to: "/knowledge", label: "Knowledge" },
];

export default function AppShell({
  children,
  title,
  back,
  focus = false,
  narrow = false,
}: {
  children: ReactNode;
  title?: string;
  back?: { to: string; label: string };
  focus?: boolean;
  narrow?: boolean;
}) {
  const location = useLocation();

  return (
    <div className={`app-shell${focus ? " app-shell--focus" : ""}`}>
      {focus && (
        <div className="app-shell__focus-tools">
          <ThemeToggle />
        </div>
      )}
      {!focus && (
        <header className="app-header">
          <div className="app-header__brand">
            <Link to="/" className="app-header__logo">
              <Logo size={28} />
              <span>Meridian</span>
            </Link>
            {title && <span className="app-header__title">{title}</span>}
          </div>
          <nav className="app-nav">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={
                  location.pathname === item.to ||
                    (item.to !== "/" && location.pathname.startsWith(item.to))
                    ? "app-nav__link app-nav__link--active"
                    : "app-nav__link"
                }
              >
                {item.label}
              </Link>
            ))}
            <ThemeToggle />
          </nav>
        </header>
      )}
      {back && (
        <Link to={back.to} className="back-link">
          {back.label}
        </Link>
      )}
      <main className={`page${narrow ? " page--narrow" : ""}`}>{children}</main>
    </div>
  );
}

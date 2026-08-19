import { useCallback, useEffect, useState } from "react";
import {
  applyTheme,
  getStoredPreference,
  resolveTheme,
  setThemePreference,
  toggleTheme,
  type ResolvedTheme,
  type ThemePreference,
} from "../lib/theme";

export function useTheme() {
  const [preference, setPreferenceState] = useState<ThemePreference>(() => getStoredPreference());
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(getStoredPreference()));

  useEffect(() => {
    if (preference !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const sync = () => {
      const next = resolveTheme("system");
      applyTheme(next);
      setResolved(next);
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, [preference]);

  const setPreference = useCallback((next: ThemePreference) => {
    const resolvedTheme = setThemePreference(next);
    setPreferenceState(next);
    setResolved(resolvedTheme);
  }, []);

  const toggle = useCallback(() => {
    const next = toggleTheme(resolved);
    setPreferenceState(next === "ink" ? "ink" : "classic");
    setResolved(next);
  }, [resolved]);

  return { preference, resolved, setPreference, toggle };
}

export type ThemePreference = "classic" | "ink" | "system";
export type ResolvedTheme = "classic" | "ink";

const STORAGE_KEY = "meridian-theme";

export function getStoredPreference(): ThemePreference {
  const value = localStorage.getItem(STORAGE_KEY);
  if (value === "classic" || value === "ink" || value === "system") {
    return value;
  }
  return "system";
}

export function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference === "classic") return "classic";
  if (preference === "ink") return "ink";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "ink" : "classic";
}

export function applyTheme(resolved: ResolvedTheme): void {
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved === "ink" ? "dark" : "light";
}

export function initTheme(): ResolvedTheme {
  const preference = getStoredPreference();
  const resolved = resolveTheme(preference);
  applyTheme(resolved);
  return resolved;
}

export function setThemePreference(preference: ThemePreference): ResolvedTheme {
  localStorage.setItem(STORAGE_KEY, preference);
  const resolved = resolveTheme(preference);
  applyTheme(resolved);
  return resolved;
}

export function toggleTheme(current: ResolvedTheme): ResolvedTheme {
  return setThemePreference(current === "ink" ? "classic" : "ink");
}

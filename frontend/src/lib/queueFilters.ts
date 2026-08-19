import type { SourceDetail } from "../api";
import { platformFromSource, type Platform } from "./platform";

const FRAMING_KEYS = [
  "display_title",
  "point",
  "matters_for_goals",
  "where_to_focus",
  "why_now",
  "skip_if",
] as const;

/** Full searchable corpus for a queue item (Phase 2 embeddings use the same fields). */
export function buildSearchableText(item: SourceDetail): string {
  const { source, scores } = item;
  const parts: string[] = [];

  if (source.title) parts.push(source.title);
  if (source.url) parts.push(source.url);
  if (source.genre) parts.push(source.genre);
  if (source.source_type) parts.push(source.source_type);
  parts.push(platformFromSource(source));

  const framing = scores?.framing;
  if (framing) {
    for (const key of FRAMING_KEYS) {
      const value = framing[key];
      if (typeof value === "string" && value.trim()) {
        parts.push(value);
      }
    }
  }

  const themes = scores?.theme_breakdown;
  if (themes) {
    for (const [theme, score] of Object.entries(themes)) {
      if (score > 0) {
        parts.push(theme.replace("/", " "));
      }
    }
  }

  if (source.normalized_text) {
    parts.push(source.normalized_text);
  }

  return parts.join("\n").toLowerCase();
}

export function filterByMedium(
  items: SourceDetail[],
  selected: Platform[],
): SourceDetail[] {
  if (selected.length === 0) return items;
  return items.filter((item) => selected.includes(platformFromSource(item.source)));
}

export function applyThemeSelection(
  items: SourceDetail[],
  theme: string | "all",
): SourceDetail[] {
  if (theme === "all") return items;
  const matched = items.filter((item) => (item.scores?.theme_breakdown?.[theme] ?? 0) > 0);
  return [...matched].sort((left, right) => {
    const leftScore = left.scores?.theme_breakdown?.[theme] ?? 0;
    const rightScore = right.scores?.theme_breakdown?.[theme] ?? 0;
    return rightScore - leftScore;
  });
}

export function applyQueueFilters(
  items: SourceDetail[],
  filters: { media: Platform[]; theme: string | "all" },
): SourceDetail[] {
  return applyThemeSelection(filterByMedium(items, filters.media), filters.theme);
}

/** Client-side keyword search until Phase 2 vector RAG. All terms must match. */
export function filterByQuery(items: SourceDetail[], query: string): SourceDetail[] {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return [];
  const terms = trimmed.split(/\s+/).filter(Boolean);
  return items.filter((item) => {
    const haystack = buildSearchableText(item);
    return terms.every((term) => haystack.includes(term));
  });
}

export function countByMedium(items: SourceDetail[]): Record<Platform, number> {
  const counts: Record<Platform, number> = {
    youtube: 0,
    lesswrong: 0,
    web: 0,
    pdf: 0,
    arxiv: 0,
  };
  for (const item of items) {
    counts[platformFromSource(item.source)] += 1;
  }
  return counts;
}

export function countByTheme(items: SourceDetail[], themeId: string): number {
  return items.filter((item) => (item.scores?.theme_breakdown?.[themeId] ?? 0) > 0).length;
}

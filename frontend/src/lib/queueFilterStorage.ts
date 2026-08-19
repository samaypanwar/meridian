import type { Platform } from "./platform";

const STORAGE_KEY = "meridian-queue-filters";

export interface StoredQueueFilters {
  media: Platform[];
  theme: string | "all";
}

const DEFAULT: StoredQueueFilters = {
  media: [],
  theme: "all",
};

export function getStoredQueueFilters(): StoredQueueFilters {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT;
    const parsed = JSON.parse(raw) as Partial<StoredQueueFilters>;
    return {
      media: Array.isArray(parsed.media) ? parsed.media : [],
      theme: typeof parsed.theme === "string" ? parsed.theme : "all",
    };
  } catch {
    return DEFAULT;
  }
}

export function setStoredQueueFilters(filters: StoredQueueFilters): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
}

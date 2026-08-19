export type QueueMode = "goals" | "curiosity";

const STORAGE_KEY = "meridian-queue-mode";

export function getStoredQueueMode(): QueueMode {
  const value = localStorage.getItem(STORAGE_KEY);
  return value === "curiosity" ? "curiosity" : "goals";
}

export function setStoredQueueMode(mode: QueueMode): void {
  localStorage.setItem(STORAGE_KEY, mode);
}

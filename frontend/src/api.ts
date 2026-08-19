export interface Source {
  id: number;
  title: string | null;
  url: string | null;
  source_type: string;
  genre: string | null;
  status: string;
  normalized_text?: string | null;
}

export interface Scores {
  relevance: number | null;
  urgency0: number | null;
  effort: number | null;
  depth_required: number | null;
  curiosity: number | null;
  theme_breakdown?: Record<string, number> | null;
  confidence: string | null;
  framing?: Record<string, string> | null;
  reading_plan?: unknown[] | null;
}

export interface SourceDetail {
  source: Source;
  scores: Scores | null;
  note_path?: string | null;
}

export interface AddSourceResponse {
  source: Source;
  scores: Scores | null;
  scoring_model: string;
  status_message: string;
}

export interface QueueResponse {
  active: SourceDetail[];
  pending: SourceDetail[];
  backlog: SourceDetail[];
  mode?: QueueMode;
}

export type QueueMode = "goals" | "curiosity";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const raw = await resp.text();
    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      if (typeof parsed.detail === "string") {
        throw new Error(parsed.detail);
      }
    } catch (error) {
      if (error instanceof Error && error.message !== raw) {
        throw error;
      }
    }
    throw new Error(raw);
  }
  return resp.json() as Promise<T>;
}

export function addSource(ref: string, transcript?: string) {
  return request<AddSourceResponse>("/sources", {
    method: "POST",
    body: JSON.stringify({ ref, transcript: transcript?.trim() || undefined }),
  });
}

export function getQueue(mode: QueueMode = "goals") {
  const query = mode === "curiosity" ? "?mode=curiosity" : "";
  return request<QueueResponse>(`/queue${query}`);
}

export function refetchSource(id: number) {
  return request<AddSourceResponse>(`/sources/${id}/refetch`, { method: "POST" });
}

export function rescoreSource(id: number) {
  return request<AddSourceResponse>(`/sources/${id}/rescore`, { method: "POST" });
}

export function pasteTranscript(id: number, text: string) {
  return request<AddSourceResponse>(`/sources/${id}/transcript`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function getSource(id: number) {
  return request<SourceDetail>(`/sources/${id}`);
}

export function capturePreview(id: number, reflection: string) {
  return request<{ preview: string; shallow: boolean }>(`/sources/${id}/capture`, {
    method: "POST",
    body: JSON.stringify({ reflection }),
  });
}

export function captureApprove(id: number, preview: string) {
  return request<{ note_path: string; status: string }>(`/sources/${id}/capture/approve`, {
    method: "POST",
    body: JSON.stringify({ preview }),
  });
}

export function kbQuery(q: string) {
  return request<{ text: string; citations: string[] }>(`/kb/query?q=${encodeURIComponent(q)}`);
}

export function getDueReviews() {
  return request<{ reviews: ReviewItem[] }>("/reviews/due");
}

export function gradeReview(id: number, grade: string) {
  return request<{ status: string }>(`/reviews/${id}/grade`, {
    method: "POST",
    body: JSON.stringify({ grade }),
  });
}

export function getCaptureDestination(id: number) {
  return request<{ note_path: string; capture_path: string }>(`/sources/${id}/capture/destination`);
}

export function getGoals() {
  return request<{
    goals_md: string;
    goals_rationale_md: string;
    capture_path: string;
    indicators: Record<string, unknown>;
  }>("/goals");
}

export interface ReviewItem {
  id: number;
  question: string;
  note_path: string;
  source_id: number | null;
}

export function displayTitle(item: SourceDetail): string {
  const framingTitle = item.scores?.framing?.display_title;
  if (typeof framingTitle === "string" && framingTitle.trim()) {
    return framingTitle.trim();
  }
  return item.source.title ?? item.source.url ?? "Untitled source";
}

export function priorityScore(scores: Scores | null): number {
  if (!scores?.relevance || !scores.urgency0 || !scores.effort) return 0;
  return (scores.relevance * scores.urgency0) / scores.effort;
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

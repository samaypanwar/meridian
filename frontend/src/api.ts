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
}

export interface QueueResponse {
  active: SourceDetail[];
}

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    throw new Error(await resp.text());
  }
  return resp.json() as Promise<T>;
}

export function addSource(ref: string) {
  return request<SourceDetail>("/sources", {
    method: "POST",
    body: JSON.stringify({ ref }),
  });
}

export function getQueue() {
  return request<QueueResponse>("/queue");
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

export function getGoals() {
  return request<{ goals_md: string; indicators: Record<string, unknown> }>("/goals");
}

export interface ReviewItem {
  id: number;
  question: string;
  note_path: string;
  source_id: number | null;
}

export function priorityScore(scores: Scores | null): number {
  if (!scores?.relevance || !scores.urgency0 || !scores.effort) return 0;
  return (scores.relevance * scores.urgency0) / scores.effort;
}

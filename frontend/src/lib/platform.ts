import type { Source } from "../api";

export type Platform = "youtube" | "lesswrong" | "web" | "pdf" | "arxiv";

const LESSWRONG_HOSTS = new Set(["lesswrong.com", "alignmentforum.org"]);

export function platformFromSource(source: Source): Platform {
  if (source.platform) {
    return source.platform as Platform;
  }
  if (source.source_type === "youtube") return "youtube";
  if (source.source_type === "pdf") return "pdf";
  if (source.source_type === "arxiv") return "arxiv";
  if (source.url) {
    try {
      const host = new URL(source.url).hostname.replace(/^www\./, "").toLowerCase();
      if (LESSWRONG_HOSTS.has(host)) return "lesswrong";
    } catch {
      /* ignore invalid URLs */
    }
  }
  return "web";
}

export const MEDIUM_OPTIONS: { id: Platform; label: string }[] = [
  { id: "youtube", label: "YouTube" },
  { id: "lesswrong", label: "LessWrong" },
  { id: "web", label: "Web" },
  { id: "pdf", label: "PDF" },
  { id: "arxiv", label: "ArXiv" },
];

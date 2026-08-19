export interface ParsedTheme {
  id: string;
  description: string;
}

export interface ParsedObjective {
  id: string;
  title: string;
  lines: string[];
}

export interface ParsedRationaleSection {
  title: string;
  body: string;
}

export interface ParsedGoals {
  cycle: string | null;
  title: string | null;
  mission: string[];
  themes: ParsedTheme[];
  objectives: ParsedObjective[];
  curiosity: string[];
  targetMix: Record<string, number>;
}

function findSection(md: string, prefix: string): string {
  const parts = md.split(/^## /m);
  for (const part of parts) {
    if (part.startsWith(prefix)) {
      const newline = part.indexOf("\n");
      return newline === -1 ? "" : part.slice(newline + 1);
    }
  }
  return "";
}

function parseObjectiveLines(rawLines: string[]): string[] {
  const items: string[] = [];
  for (const line of rawLines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("<!--")) continue;
    if (trimmed.startsWith("- ")) {
      items.push(trimmed.slice(2).trim());
      continue;
    }
    if (items.length > 0) {
      items[items.length - 1] = `${items[items.length - 1]} ${trimmed}`;
    }
  }
  return items;
}

function bulletItems(block: string): string[] {
  return block
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("- "))
    .map((line) => line.slice(2).trim())
    .filter((line) => line && !line.startsWith("<!--"));
}

/** Parse `- \`theme/id\` — description` or plain `- theme/id — description`. */
export function parseThemeLine(line: string): ParsedTheme | null {
  const trimmed = line.trim();
  if (!trimmed) return null;

  const rich = trimmed.match(/^`([^`]+)`\s*[—–-]\s*(.+)$/);
  if (rich) {
    return { id: rich[1].trim(), description: rich[2].trim() };
  }

  const plain = trimmed.match(/^([a-z]+\/[\w-]+)\s*[—–-]\s*(.+)$/i);
  if (plain) {
    return { id: plain[1].trim(), description: plain[2].trim() };
  }

  const idOnly = trimmed.replace(/^`|`$/g, "").trim();
  if (idOnly.includes("/")) {
    return { id: idOnly, description: "" };
  }

  return null;
}

function parseThemes(block: string): ParsedTheme[] {
  return bulletItems(block)
    .map(parseThemeLine)
    .filter((theme): theme is ParsedTheme => theme !== null);
}

export function parseRationaleMd(md: string): ParsedRationaleSection[] {
  if (!md.trim()) return [];

  const parts = md.split(/^## /m).slice(1);
  return parts.map((part) => {
    const newline = part.indexOf("\n");
    const title = (newline === -1 ? part : part.slice(0, newline)).trim();
    const body = (newline === -1 ? "" : part.slice(newline + 1)).trim();
    return { title, body };
  });
}

export function parseGoalsMd(md: string): ParsedGoals {
  const cycleMatch = md.match(/^cycle:\s*(.+)$/m);
  const titleMatch = md.match(/^#\s+(.+)$/m);
  const mixMatch = md.match(/target_mix:\s*\{([^}]+)\}/);
  const targetMix: Record<string, number> = {};
  if (mixMatch) {
    for (const part of mixMatch[1].split(",")) {
      const [key, raw] = part.split(":").map((s) => s.trim());
      if (key && raw) targetMix[key] = Number(raw);
    }
  }

  const missionBlock = findSection(md, "Mission");
  const themesBlock = findSection(md, "Themes");
  const objectivesBlock = findSection(md, "This cycle");
  const curiosityBlock = findSection(md, "Curiosity");

  const objectives: ParsedObjective[] = [];
  const objParts = objectivesBlock.split(/^### /m).slice(1);
  for (const part of objParts) {
    const [head, ...rest] = part.split("\n");
    const title = head?.trim() ?? "Objective";
    const idMatch = title.match(/^(O\d+)/);
    objectives.push({
      id: idMatch?.[1] ?? title,
      title,
      lines: parseObjectiveLines(rest),
    });
  }

  return {
    cycle: cycleMatch?.[1]?.trim() ?? null,
    title: titleMatch?.[1]?.trim() ?? null,
    mission: bulletItems(missionBlock),
    themes: parseThemes(themesBlock),
    objectives,
    curiosity: bulletItems(curiosityBlock),
    targetMix,
  };
}

export interface IndicatorTargets {
  capturesPerCycle: number;
  reviewPassRate: number;
  hoursPerWeek: number;
}

export function defaultIndicatorTargets(): IndicatorTargets {
  return {
    capturesPerCycle: 3,
    reviewPassRate: 0.8,
    hoursPerWeek: 4,
  };
}

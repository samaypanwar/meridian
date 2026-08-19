export interface ParsedObjective {
  id: string;
  title: string;
  lines: string[];
}

export interface ParsedGoals {
  cycle: string | null;
  mission: string[];
  themes: string[];
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

export function parseGoalsMd(md: string): ParsedGoals {
  const cycleMatch = md.match(/^cycle:\s*(.+)$/m);
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
    mission: bulletItems(missionBlock),
    themes: bulletItems(themesBlock),
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

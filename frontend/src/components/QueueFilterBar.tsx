import type { KeyboardEvent } from "react";
import type { ParsedTheme } from "../lib/goalsParse";
import { MEDIUM_OPTIONS, type Platform } from "../lib/platform";
import { countByMedium, countByTheme } from "../lib/queueFilters";
import type { SourceDetail } from "../api";

interface QueueFilterBarProps {
  queueItems: SourceDetail[];
  themes: ParsedTheme[];
  selectedMedia: Platform[];
  selectedTheme: string | "all";
  searchInput: string;
  searchBusy?: boolean;
  onMediaChange: (media: Platform[]) => void;
  onThemeChange: (theme: string | "all") => void;
  onSearchInputChange: (value: string) => void;
  onSearchSubmit: () => void;
  onClearSearch: () => void;
}

function toggleMedium(current: Platform[], platform: Platform): Platform[] {
  if (current.includes(platform)) {
    return current.filter((entry) => entry !== platform);
  }
  return [...current, platform];
}

export default function QueueFilterBar({
  queueItems,
  themes,
  selectedMedia,
  selectedTheme,
  searchInput,
  searchBusy = false,
  onMediaChange,
  onThemeChange,
  onSearchInputChange,
  onSearchSubmit,
  onClearSearch,
}: QueueFilterBarProps) {
  const mediumCounts = countByMedium(queueItems);
  const mediaActive = selectedMedia.length > 0;

  function onSearchKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      onSearchSubmit();
    }
  }

  return (
    <div className="queue-filter-bar">
      <div className="queue-filter-bar__row">
        <span className="queue-filter-bar__label">Medium</span>
        <div className="queue-filter-bar__chips" role="group" aria-label="Filter by medium">
          <button
            type="button"
            className={`filter-chip${!mediaActive ? " filter-chip--active" : ""}`}
            onClick={() => onMediaChange([])}
          >
            All
          </button>
          {MEDIUM_OPTIONS.map((option) => {
            const count = mediumCounts[option.id];
            const active = selectedMedia.includes(option.id);
            return (
              <button
                key={option.id}
                type="button"
                className={`filter-chip${active ? " filter-chip--active" : ""}`}
                onClick={() => onMediaChange(toggleMedium(selectedMedia, option.id))}
              >
                {option.label}
                {count > 0 ? ` (${count})` : ""}
              </button>
            );
          })}
        </div>
      </div>

      {themes.length > 0 && (
        <div className="queue-filter-bar__row">
          <span className="queue-filter-bar__label">Theme</span>
          <div className="queue-filter-bar__chips" role="group" aria-label="Filter and sort by theme">
            <button
              type="button"
              className={`filter-chip${selectedTheme === "all" ? " filter-chip--active" : ""}`}
              onClick={() => onThemeChange("all")}
            >
              All
            </button>
            {themes.map((theme) => {
              const count = countByTheme(queueItems, theme.id);
              const shortId = theme.id.split("/").pop() ?? theme.id;
              const active = selectedTheme === theme.id;
              return (
                <button
                  key={theme.id}
                  type="button"
                  title={theme.description || theme.id}
                  className={`filter-chip${active ? " filter-chip--active" : ""}`}
                  onClick={() => onThemeChange(theme.id)}
                >
                  {shortId}
                  {count > 0 ? ` (${count})` : ""}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <form
        className="queue-filter-bar__search add-bar"
        onSubmit={(event) => {
          event.preventDefault();
          onSearchSubmit();
        }}
      >
        <input
          value={searchInput}
          onChange={(event) => onSearchInputChange(event.target.value)}
          onKeyDown={onSearchKeyDown}
          placeholder="Search queue — title, summary, themes, full text…"
          aria-label="Search queue sources"
        />
        <button type="submit" className="btn btn--primary" disabled={searchBusy}>
          {searchBusy ? "Searching…" : "Search"}
        </button>
        {searchInput.trim() && (
          <button type="button" className="btn" onClick={onClearSearch}>
            Clear
          </button>
        )}
      </form>
    </div>
  );
}

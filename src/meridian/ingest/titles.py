from __future__ import annotations

import re
from urllib.parse import urlparse


_GITHUB_PREFIX = re.compile(r"^GitHub\s*[-–—]\s*", re.IGNORECASE)
_GITHUB_SUFFIXES = (" · GitHub", " on GitHub", " - GitHub")


def clean_extracted_title(title: str, url: str | None = None) -> str:
    cleaned = title.strip()
    if not cleaned:
        return cleaned

    cleaned = _GITHUB_PREFIX.sub("", cleaned)
    for suffix in _GITHUB_SUFFIXES:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()

    if url:
        host = urlparse(url).netloc.removeprefix("www.").lower()
        if host == "github.com":
            cleaned = _clean_github_title(cleaned, url)

    return cleaned.strip() or title.strip()


def _clean_github_title(title: str, url: str) -> str:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2:
        repo = f"{parts[0]}/{parts[1]}"
        if title.lower().startswith(repo.lower()):
            remainder = title[len(parts[0]) + 1 + len(parts[1]) :].lstrip(" :-–—")
            if remainder:
                return f"{repo}: {remainder}"
            return repo
        if ":" in title:
            return title
        return f"{repo}: {title}" if title != repo else repo
    return title

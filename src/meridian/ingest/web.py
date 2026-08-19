from __future__ import annotations

from pathlib import Path
from typing import Any

import trafilatura


def fetch_text(url: str) -> tuple[str, dict[str, Any]]:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Failed to fetch {url}")
    text = trafilatura.extract(downloaded) or ""
    words = len(text.split())
    return text, {"words": words, "url": url}

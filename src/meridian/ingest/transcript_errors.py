from __future__ import annotations

from typing import Any


class YouTubeTranscriptBlocked(Exception):
    """YouTube refused transcript fetch (IP block, rate limit, etc.)."""

    def __init__(self, meta: dict[str, Any], reason: str = "blocked") -> None:
        self.meta = meta
        self.reason = reason
        super().__init__(
            "YouTube blocked the transcript request from this network. "
            "Meridian can still score from the video title, or you can paste a transcript."
        )

from __future__ import annotations

from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi


def fetch_captions(url: str) -> tuple[str, dict[str, Any]]:
    video_id = _video_id_from_url(url)
    api = YouTubeTranscriptApi()
    segments = api.fetch(video_id)
    text = " ".join(segment["text"] for segment in segments)
    last = segments[-1]
    minutes = (last["start"] + last["duration"]) / 60.0
    return text, {"minutes": round(minutes, 2), "segments": len(segments)}


def _video_id_from_url(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return url.rstrip("/").split("/")[-1]

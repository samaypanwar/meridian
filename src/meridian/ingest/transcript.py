from __future__ import annotations

import re
from typing import Any

import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

from meridian.ingest.transcript_errors import YouTubeTranscriptBlocked

_WATCH_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_OG_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]+)"')
_CHANNEL_NAME_RE = re.compile(r'"ownerChannelName":"([^"\\]+)"')


def fetch_captions(url: str) -> tuple[str, dict[str, Any]]:
    video_id = _video_id_from_url(url)
    meta = fetch_video_meta(url)
    try:
        api = YouTubeTranscriptApi()
        raw_segments = api.fetch(video_id)
    except (IpBlocked, RequestBlocked) as exc:
        raise YouTubeTranscriptBlocked(meta, reason="blocked") from exc
    except TranscriptsDisabled as exc:
        raise YouTubeTranscriptBlocked(meta, reason="disabled") from exc
    except NoTranscriptFound as exc:
        raise YouTubeTranscriptBlocked(meta, reason="missing") from exc
    except VideoUnavailable as exc:
        raise ValueError("This YouTube video is unavailable or private.") from exc
    except CouldNotRetrieveTranscript as exc:
        raise ValueError(f"Could not fetch YouTube transcript: {exc}") from exc

    segments = list(raw_segments)
    if not segments:
        raise YouTubeTranscriptBlocked(meta, reason="empty")

    text = " ".join(_segment_text(segment) for segment in segments).strip()
    if not text:
        raise YouTubeTranscriptBlocked(meta, reason="empty")

    last = segments[-1]
    minutes = (_segment_start(last) + _segment_duration(last)) / 60.0
    meta.update(
        {
            "minutes": round(minutes, 2),
            "segments": len(segments),
            "words": len(text.split()),
            "engine": "youtube_transcript_api",
            "transcript_status": "ok",
        }
    )
    return text, meta


def fetch_video_meta(url: str) -> dict[str, Any]:
    meta: dict[str, Any] = {"url": url}
    oembed = _fetch_oembed_meta(url)
    if oembed:
        meta.update(oembed)
        return meta

    watch = _fetch_watch_page_meta(url)
    meta.update(watch)
    if "title" not in meta:
        meta["title"] = _video_id_from_url(url)
    return meta


def _fetch_oembed_meta(url: str) -> dict[str, Any]:
    try:
        response = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=30.0,
            follow_redirects=True,
        )
        if not response.is_success:
            return {}
        payload = response.json()
    except httpx.HTTPError:
        return {}

    meta: dict[str, Any] = {"meta_engine": "youtube_oembed"}
    if payload.get("title"):
        meta["title"] = payload["title"]
    if payload.get("author_name"):
        meta["author"] = payload["author_name"]
    return meta


def _fetch_watch_page_meta(url: str) -> dict[str, Any]:
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": _WATCH_USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return {}

    html = response.text
    meta: dict[str, Any] = {"meta_engine": "youtube_watch_page"}
    title_match = _OG_TITLE_RE.search(html)
    if title_match:
        meta["title"] = title_match.group(1)
    channel_match = _CHANNEL_NAME_RE.search(html)
    if channel_match:
        meta["author"] = channel_match.group(1)
    return meta


def _segment_text(segment: Any) -> str:
    if isinstance(segment, dict):
        return str(segment["text"])
    return str(segment.text)


def _segment_start(segment: Any) -> float:
    if isinstance(segment, dict):
        return float(segment["start"])
    return float(segment.start)


def _segment_duration(segment: Any) -> float:
    if isinstance(segment, dict):
        return float(segment["duration"])
    return float(segment.duration)


def _video_id_from_url(url: str) -> str:
    if "youtu.be/" in url:
        return url.split("youtu.be/", 1)[1].split("?")[0].split("/")[0]
    if "v=" in url:
        return url.split("v=", 1)[1].split("&")[0]
    return url.rstrip("/").split("/")[-1]

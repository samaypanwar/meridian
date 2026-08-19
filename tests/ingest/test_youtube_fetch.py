from unittest.mock import patch

import httpx
from youtube_transcript_api._errors import IpBlocked
from youtube_transcript_api._transcripts import FetchedTranscriptSnippet

from meridian.ingest import transcript
from meridian.ingest.fetch import fetch_normalized
from meridian.ingest.transcript_errors import YouTubeTranscriptBlocked


def test_fetch_youtube_blocked_returns_metadata_only() -> None:
    url = "https://www.youtube.com/watch?v=abc"
    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "RL Talk", "author": "Channel"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            side_effect=IpBlocked(url),
        ):
            text, meta, resolved = fetch_normalized(url, "youtube")
    assert text == ""
    assert meta["transcript_status"] == "blocked"
    assert meta["title"] == "RL Talk"
    assert resolved == url


def test_fetch_captions_raises_blocked_with_meta() -> None:
    from meridian.ingest import transcript

    url = "https://www.youtube.com/watch?v=abc"
    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "RL Talk"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            side_effect=IpBlocked(url),
        ):
            try:
                transcript.fetch_captions(url)
            except YouTubeTranscriptBlocked as exc:
                assert exc.meta["title"] == "RL Talk"
                assert exc.reason == "blocked"
            else:
                raise AssertionError("expected YouTubeTranscriptBlocked")


def test_fetch_video_meta_falls_back_when_oembed_unauthorized() -> None:
    url = "https://www.youtube.com/watch?v=6YnLB0XbTnI"

    class FakeResponse:
        status_code = 401
        is_success = False

        def json(self) -> dict:
            return {}

    watch_html = (
        '<meta property="og:title" content="Stanford CS329A Self-Improving AI Agents">'
        '"ownerChannelName":"Stanford Online"'
    )

    class WatchResponse:
        def raise_for_status(self) -> None:
            return None

        text = watch_html

    with patch(
        "meridian.ingest.transcript.httpx.get",
        side_effect=[FakeResponse(), WatchResponse()],
    ):
        meta = transcript.fetch_video_meta(url)

    assert meta["title"] == "Stanford CS329A Self-Improving AI Agents"
    assert meta["author"] == "Stanford Online"
    assert meta["meta_engine"] == "youtube_watch_page"


def test_fetch_captions_works_when_oembed_unauthorized() -> None:
    url = "https://www.youtube.com/watch?v=6YnLB0XbTnI"
    snippets = [
        FetchedTranscriptSnippet("Welcome to CS329A.", 0.0, 3.0),
        FetchedTranscriptSnippet("This is the course overview.", 3.0, 4.0),
    ]

    class FakeResponse:
        status_code = 401
        is_success = False

        def json(self) -> dict:
            return {}

    watch_html = '<meta property="og:title" content="Stanford CS329A Course Overview">'

    class WatchResponse:
        def raise_for_status(self) -> None:
            return None

        text = watch_html

    with patch(
        "meridian.ingest.transcript.httpx.get",
        side_effect=[FakeResponse(), WatchResponse()],
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            return_value=snippets,
        ):
            text, meta = transcript.fetch_captions(url)

    assert "course overview" in text.lower()
    assert meta["title"] == "Stanford CS329A Course Overview"
    assert meta["transcript_status"] == "ok"

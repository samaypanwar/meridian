from unittest.mock import patch

from youtube_transcript_api._errors import IpBlocked

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

from unittest.mock import patch

from youtube_transcript_api._transcripts import FetchedTranscriptSnippet

from meridian.ingest import transcript
from meridian.ingest.titles import clean_extracted_title


def test_clean_github_title() -> None:
    url = "https://github.com/openai/spinningup"
    raw = "GitHub - openai/spinningup: An educational resource for RL"
    cleaned = clean_extracted_title(raw, url)
    assert cleaned == "openai/spinningup: An educational resource for RL"


def test_clean_github_suffix() -> None:
    cleaned = clean_extracted_title("Some repo · GitHub")
    assert cleaned == "Some repo"


def test_transcript_handles_fetched_transcript_snippets() -> None:
    snippets = [
        FetchedTranscriptSnippet("Welcome to reinforcement learning.", 0.0, 3.0),
        FetchedTranscriptSnippet(
            "Today we cover the policy gradient theorem.", 3.0, 4.0
        ),
    ]
    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "RL Talk"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            return_value=snippets,
        ):
            text, meta = transcript.fetch_captions("https://youtube.com/watch?v=abc")
    assert "policy gradient" in text.lower()
    assert meta["title"] == "RL Talk"
    assert meta["minutes"] > 0

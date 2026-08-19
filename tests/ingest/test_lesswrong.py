import json
from unittest.mock import patch

import httpx

from meridian.ingest import lesswrong


def test_fetch_lesswrong_post_returns_title_and_markdown() -> None:
    payload = {
        "data": {
            "post": {
                "result": {
                    "title": "Science as Attire",
                    "postedAt": "2008-08-23T07:00:00.000Z",
                    "user": {"displayName": "Eliezer Yudkowsky"},
                    "contents": {
                        "markdown": "The preview for the X-Men movie has a voice-over."
                    },
                }
            }
        }
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return payload

    with patch("meridian.ingest.lesswrong.httpx.post", return_value=FakeResponse()):
        text, meta = lesswrong.fetch_text(
            "https://www.lesswrong.com/s/seq/p/4Bwr6s9dofvqPWakn"
        )

    assert "X-Men" in text
    assert meta["title"] == "Science as Attire"
    assert meta["author"] == "Eliezer Yudkowsky"
    assert meta["engine"] == "lesswrong-graphql"


def test_post_id_from_modern_posts_url() -> None:
    assert (
        lesswrong.post_id_from_url("https://www.lesswrong.com/posts/uMQ3cqWDPHhjtiesc")
        == "uMQ3cqWDPHhjtiesc"
    )


def test_post_id_from_legacy_sequence_url() -> None:
    assert (
        lesswrong.post_id_from_url(
            "https://www.lesswrong.com/s/seq/p/4Bwr6s9dofvqPWakn"
        )
        == "4Bwr6s9dofvqPWakn"
    )


def test_fetch_lesswrong_posts_url_returns_title_and_markdown() -> None:
    payload = {
        "data": {
            "post": {
                "result": {
                    "title": "AGI Ruin: A List of Lethalities",
                    "postedAt": "2022-06-06T07:00:00.000Z",
                    "user": {"displayName": "Eliezer Yudkowsky"},
                    "contents": {"markdown": "Preamble about AGI alignment."},
                }
            }
        }
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return payload

    with patch("meridian.ingest.lesswrong.httpx.post", return_value=FakeResponse()):
        text, meta = lesswrong.fetch_text(
            "https://www.lesswrong.com/posts/uMQ3cqWDPHhjtiesc"
        )

    assert "Preamble" in text
    assert meta["title"] == "AGI Ruin: A List of Lethalities"
    assert meta["engine"] == "lesswrong-graphql"

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import fitz
import pytest

from meridian.ingest import pdf, transcript, web


def test_web_fetch_text_returns_content() -> None:
    html = (
        "<html><body><article><p>Hello Meridian web text.</p></article></body></html>"
    )
    with patch("meridian.ingest.web.trafilatura.fetch_url", return_value=html):
        with patch(
            "meridian.ingest.web.trafilatura.extract",
            return_value="Hello Meridian web text.",
        ):
            text, meta = web.fetch_text("https://example.com/article")
    assert text
    assert meta["words"] >= 1


def test_pdf_extract_text_from_fixture(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello Meridian PDF text.")
    doc.save(pdf_path)
    doc.close()

    text, meta = pdf.extract_text(pdf_path)
    assert "Meridian PDF" in text
    assert meta["pages"] == 1
    assert meta["words"] >= 3


def test_transcript_fetch_captions_from_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "youtube_captions.json"
    captions = json.loads(fixture.read_text())
    with patch(
        "meridian.ingest.transcript.fetch_video_meta",
        return_value={"title": "RL Talk"},
    ):
        with patch(
            "meridian.ingest.transcript.YouTubeTranscriptApi.fetch",
            return_value=captions,
        ):
            text, meta = transcript.fetch_captions("https://youtube.com/watch?v=abc")
    assert "policy gradient" in text.lower()
    assert meta["minutes"] > 0

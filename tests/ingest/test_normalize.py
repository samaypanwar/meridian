import pytest

from meridian.ingest import normalize


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        ("https://example.com/paper.pdf?download=1", "pdf"),
        ("https://arxiv.org/abs/2301.00001", "arxiv"),
        ("/path/to/paper.pdf", "pdf"),
        ("paper.pdf", "pdf"),
        ("https://www.youtube.com/watch?v=abc123", "youtube"),
        ("https://example.com/article", "web"),
    ],
)
def test_detect_type(ref: str, expected: str) -> None:
    assert normalize.detect_type(ref) == expected


def test_ingest_dispatches_and_returns_source() -> None:
    source = normalize.ingest("https://example.com/article")
    assert source.source_type == "web"
    assert source.status == "queued"

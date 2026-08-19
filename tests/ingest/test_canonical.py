from meridian.ingest.canonical import canonical_ref


def test_canonical_youtube_watch_and_short_link() -> None:
    watch = "https://www.youtube.com/watch?v=abc123XYZ_-"
    short = "https://youtu.be/abc123XYZ_-?t=120"
    assert canonical_ref(watch) == canonical_ref(short) == "youtube:abc123XYZ_-"


def test_canonical_lesswrong_post_and_legacy_urls() -> None:
    modern = "https://www.lesswrong.com/posts/uMQ3cqWDPHhjtiesc"
    legacy = "https://www.lesswrong.com/s/seq/p/uMQ3cqWDPHhjtiesc"
    assert (
        canonical_ref(modern) == canonical_ref(legacy) == "lesswrong:uMQ3cqWDPHhjtiesc"
    )


def test_canonical_arxiv_abs_url() -> None:
    url = "https://arxiv.org/abs/2301.12345v2?utm_source=twitter"
    assert canonical_ref(url) == "arxiv:2301.12345"


def test_canonical_web_strips_tracking_params() -> None:
    a = "https://Example.com/article?utm_campaign=x&id=1"
    b = "https://www.example.com/article?id=1"
    assert canonical_ref(a) == canonical_ref(b)


def test_canonical_pdf_url_normalizes() -> None:
    a = "https://Example.com/paper.pdf?utm_source=email"
    b = "https://www.example.com/paper.pdf"
    assert canonical_ref(a) == canonical_ref(b) == "pdf:https://example.com/paper.pdf"

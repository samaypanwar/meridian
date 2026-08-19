from meridian.ingest.platform import platform_for_source


def test_platform_youtube() -> None:
    assert (
        platform_for_source(
            url="https://www.youtube.com/watch?v=abc",
            source_type="youtube",
        )
        == "youtube"
    )


def test_platform_lesswrong_posts_url() -> None:
    assert (
        platform_for_source(
            url="https://www.lesswrong.com/posts/uMQ3cqWDPHhjtiesc",
            source_type="web",
        )
        == "lesswrong"
    )


def test_platform_alignment_forum() -> None:
    assert (
        platform_for_source(
            url="https://www.alignmentforum.org/posts/abc123",
            source_type="web",
        )
        == "lesswrong"
    )


def test_platform_plain_web() -> None:
    assert (
        platform_for_source(
            url="https://example.com/article",
            source_type="web",
        )
        == "web"
    )


def test_platform_pdf_and_arxiv() -> None:
    assert platform_for_source(url=None, source_type="pdf") == "pdf"
    assert (
        platform_for_source(
            url="https://arxiv.org/abs/1234.5678",
            source_type="arxiv",
        )
        == "arxiv"
    )

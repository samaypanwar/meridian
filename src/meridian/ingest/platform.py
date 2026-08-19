from __future__ import annotations

from urllib.parse import urlparse

LESSWRONG_HOSTS = frozenset({"lesswrong.com", "alignmentforum.org"})


def platform_for_source(*, url: str | None, source_type: str) -> str:
    if source_type == "youtube":
        return "youtube"
    if source_type == "pdf":
        return "pdf"
    if source_type == "arxiv":
        return "arxiv"
    if url:
        host = urlparse(url).netloc.removeprefix("www.").lower()
        if host in LESSWRONG_HOSTS:
            return "lesswrong"
    if source_type == "web":
        return "web"
    return source_type

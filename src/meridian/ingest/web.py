from __future__ import annotations

from typing import Any

import httpx
import trafilatura

from meridian.ingest.titles import clean_extracted_title

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


def fetch_text(url: str) -> tuple[str, dict[str, Any]]:
    html = _download_html(url)
    text = trafilatura.extract(html, url=url, include_comments=False) or ""
    if not text.strip():
        raise ValueError(f"No readable text extracted from {url}")

    meta: dict[str, Any] = {
        "words": len(text.split()),
        "url": url,
        "engine": "trafilatura",
    }
    extracted = trafilatura.extract_metadata(html, default_url=url)
    if extracted:
        if extracted.title:
            meta["title"] = extracted.title
        if extracted.author:
            meta["author"] = extracted.author
        if extracted.date:
            meta["date"] = extracted.date
    if "title" not in meta:
        meta["title"] = _title_from_html(html) or url
    if meta.get("title"):
        meta["title"] = clean_extracted_title(str(meta["title"]), url)
    return text, meta


def _download_html(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return downloaded

    response = httpx.get(
        url, headers=DEFAULT_HEADERS, follow_redirects=True, timeout=60.0
    )
    response.raise_for_status()
    if response.status_code >= 400:
        raise ValueError(f"HTTP {response.status_code} fetching {url}")
    return response.text


def _title_from_html(html: str) -> str | None:
    metadata = trafilatura.extract_metadata(html)
    return metadata.title if metadata and metadata.title else None

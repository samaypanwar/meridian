from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz
import httpx


def extract_text(path: Path | str) -> tuple[str, dict[str, Any]]:
    ref = str(path).strip()
    if ref.lower().startswith(("http://", "https://")):
        pdf_bytes = _download_pdf(ref)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    else:
        local = Path(ref).expanduser().resolve()
        if not local.is_file():
            raise FileNotFoundError(f"PDF not found: {local}")
        doc = fitz.open(local)

    try:
        pages = [page.get_text() for page in doc]
        doc_meta = doc.metadata or {}
    finally:
        doc.close()

    text = "\n".join(pages).strip()
    meta: dict[str, Any] = {
        "pages": len(pages),
        "words": len(text.split()),
    }
    title = (doc_meta.get("title") or "").strip()
    if title:
        meta["title"] = title
    author = (doc_meta.get("author") or "").strip()
    if author:
        meta["author"] = author
    if ref.lower().startswith(("http://", "https://")):
        meta["pdf_url"] = ref
    return text, meta


def _download_pdf(url: str) -> bytes:
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    content_type = (resp.headers.get("content-type") or "").lower()
    path_lower = url.lower().split("?", 1)[0]
    if "pdf" not in content_type and not path_lower.endswith(".pdf"):
        raise ValueError(
            f"URL did not return a PDF (content-type: {content_type or 'unknown'})"
        )
    if len(resp.content) < 100:
        raise ValueError("Downloaded PDF is too small to be valid")
    return resp.content

from __future__ import annotations

import re
from typing import Any

from meridian.ingest import pdf

_ARXIV_ID = re.compile(r"(\d{4}\.\d{4,5})(?:v\d+)?")


def arxiv_id_from_ref(ref: str) -> str | None:
    match = _ARXIV_ID.search(ref)
    return match.group(1) if match else None


def pdf_url_for_id(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def pdf_url_for_ref(ref: str) -> str:
    arxiv_id = arxiv_id_from_ref(ref)
    if arxiv_id is None:
        raise ValueError(f"Could not parse arXiv ID from: {ref}")
    return pdf_url_for_id(arxiv_id)


def fetch_text(ref: str) -> tuple[str, dict[str, Any]]:
    arxiv_id = arxiv_id_from_ref(ref)
    if arxiv_id is None:
        raise ValueError(f"Could not parse arXiv ID from: {ref}")
    pdf_url = pdf_url_for_id(arxiv_id)
    text, meta = pdf.extract_text(pdf_url)
    meta["arxiv_id"] = arxiv_id
    meta["pdf_url"] = pdf_url
    return text, meta

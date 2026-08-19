from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz


def extract_text(path: Path | str) -> tuple[str, dict[str, Any]]:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    text = "\n".join(pages).strip()
    word_count = len(text.split())
    return text, {"pages": len(pages), "words": word_count}

from unittest.mock import patch

import fitz

from meridian.ingest import arxiv, fetch


def test_arxiv_pdf_url_for_abs_link() -> None:
    assert (
        arxiv.pdf_url_for_ref("https://arxiv.org/abs/1512.02595")
        == "https://arxiv.org/pdf/1512.02595.pdf"
    )


def test_fetch_normalized_resolves_arxiv_abs_to_pdf() -> None:
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    page.insert_text((72, 72), "Deep Speech 2 end-to-end recognition.")
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    ref = "https://arxiv.org/abs/1512.02595"
    with patch(
        "meridian.ingest.pdf.httpx.get",
        return_value=type(
            "Resp",
            (),
            {
                "status_code": 200,
                "content": pdf_bytes,
                "headers": {"content-type": "application/pdf"},
                "raise_for_status": lambda self: None,
            },
        )(),
    ):
        text, meta, url = fetch.fetch_normalized(ref, "arxiv")

    assert url == ref
    assert meta["arxiv_id"] == "1512.02595"
    assert meta["pdf_url"] == "https://arxiv.org/pdf/1512.02595.pdf"
    assert "deep speech" in text.lower()

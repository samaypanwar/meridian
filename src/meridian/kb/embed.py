from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meridian.config import Settings

_model = None


def embed_texts(
    texts: list[str], *, settings: Settings | None = None
) -> list[list[float]]:
    if not texts:
        return []
    dim = 384
    if settings is None or settings.embed_model == "stub":
        return [_stub_vector(t, dim) for t in texts]
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed in this environment. "
                "Run: poetry install"
            ) from exc

        model_name = (
            settings.embed_model
            if settings
            else "sentence-transformers/all-MiniLM-L6-v2"
        )
        _model = SentenceTransformer(model_name)
    encoded = _model.encode(texts, normalize_embeddings=True)
    return [vec.tolist() for vec in encoded]


def _stub_vector(text: str, dim: int) -> list[float]:
    import hashlib

    digest = hashlib.sha256(text.encode()).digest()
    values = []
    for i in range(dim):
        values.append(((digest[i % len(digest)] / 255.0) * 2) - 1)
    return values

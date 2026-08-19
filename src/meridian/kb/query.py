from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlite_vec import serialize_float32

from meridian.config import Settings
from meridian.kb import embed
from meridian.llm import client


@dataclass
class Answer:
    text: str
    citations: list[str]


def believe(conn: Any, question: str, *, settings: Settings | None = None) -> Answer:
    settings = settings or Settings(vault_path=Path("data"), embed_model="stub")
    q_vec = embed.embed_texts([question], settings=settings)[0]
    rows = conn.execute(
        """
        SELECT m.note_path, m.chunk_text, e.distance
        FROM emb e
        JOIN emb_meta m ON m.rowid = e.rowid
        WHERE e.embedding MATCH ?
          AND k = 5
        ORDER BY e.distance
        """,
        (serialize_float32(q_vec),),
    ).fetchall()
    if not rows:
        return Answer(text="No captures found.", citations=[])

    chunks = [{"note_path": r["note_path"], "text": r["chunk_text"]} for r in rows]
    citations = list(dict.fromkeys(r["note_path"] for r in rows))
    messages = [
        {
            "role": "system",
            "content": "Synthesize what the user believes based only on the provided capture chunks. Cite note paths inline.",
        },
        {
            "role": "user",
            "content": f"Question: {question}\n\nChunks:\n{chunks}",
        },
    ]
    try:
        result = client.chat(messages)
        text = result if isinstance(result, str) else result.get("answer", str(result))
    except Exception:
        text = chunks[0]["text"]
    return Answer(text=str(text), citations=citations)

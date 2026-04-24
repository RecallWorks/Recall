# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | chunking + file ingestion | prev: NEW
"""Text chunking + single-file indexing helpers."""
from __future__ import annotations

import hashlib
from datetime import datetime

from .store import Store


def chunk_text(text: str, source: str, chunk_size: int, chunk_overlap: int) -> list[dict]:
    """Split text into overlapping chunks. Returns a list of {id, text, source, chunk_index}."""
    chunks: list[dict] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunk_id = hashlib.sha256(f"{source}:{idx}".encode()).hexdigest()[:16]
        chunks.append({"id": chunk_id, "text": chunk, "source": source, "chunk_index": idx})
        start += chunk_size - chunk_overlap
        idx += 1
    return chunks


def index_file(store: Store, filepath: str, chunk_size: int, chunk_overlap: int) -> int:
    """Read filepath, chunk it, upsert to store. Returns number of chunks indexed."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return 0
    if not content.strip():
        return 0
    chunks = chunk_text(content, filepath, chunk_size, chunk_overlap)
    batch_size = 40
    indexed_at = datetime.now().isoformat()
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        store.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "source": c["source"],
                "chunk_index": c["chunk_index"],
                "indexed_at": indexed_at,
            } for c in batch],
        )
    return len(chunks)

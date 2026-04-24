# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — in-memory Store fake for unit tests | prev: NEW
"""In-memory store implementing the Store protocol — used by unit tests
to avoid spinning up ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _Row:
    id: str
    document: str
    metadata: dict


@dataclass
class FakeStore:
    rows: dict[str, _Row] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.rows)

    def upsert(self, ids, documents, metadatas) -> None:
        for i, doc, meta in zip(ids, documents, metadatas, strict=False):
            self.rows[i] = _Row(id=i, document=doc, metadata=dict(meta))

    def query(self, query_texts, n_results, where=None):
        # Naive: return rows matching `where` (if any), in insertion order.
        results = list(self.rows.values())
        if where:
            results = [r for r in results if all(r.metadata.get(k) == v for k, v in where.items())]
        results = results[:n_results]
        return {
            "documents": [[r.document for r in results]],
            "metadatas": [[r.metadata for r in results]],
            "distances": [[0.0 for _ in results]],
            "ids": [[r.id for r in results]],
        }

    def get(self, where=None, limit=100, include=None):
        results = list(self.rows.values())
        if where:
            results = [r for r in results if all(r.metadata.get(k) == v for k, v in where.items())]
        results = results[:limit]
        return {
            "ids": [r.id for r in results],
            "documents": [r.document for r in results],
            "metadatas": [r.metadata for r in results],
        }

    def delete(self, ids) -> None:
        for i in ids:
            self.rows.pop(i, None)


def install(monkeypatch=None) -> FakeStore:
    """Install a FakeStore as the module-level singleton in recall.store.

    If monkeypatch is provided (pytest fixture), uses it; otherwise mutates directly.
    """
    from recall import store as store_mod

    fake = FakeStore()
    if monkeypatch is not None:
        monkeypatch.setattr(store_mod, "_store", fake)
    else:
        store_mod._store = fake
    return fake

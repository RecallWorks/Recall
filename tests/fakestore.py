# @wbx-modified copilot-b1c4 | 2026-04-27 19:30 MTN | v1.1 | added $and/$or/$gte where ops + backfill helpers | prev: copilot-c4a1@2026-04-23
"""In-memory store implementing the Store protocol — used by unit tests
to avoid spinning up ChromaDB."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class _Row:
    id: str
    document: str
    metadata: dict


def _match_clause(meta: dict, clause: dict) -> bool:
    """Evaluate a where-clause against a metadata dict.

    Supports: equality {"k": v}, $and, $or, and {"$gte": n} numeric ops.
    """
    if "$and" in clause:
        return all(_match_clause(meta, c) for c in clause["$and"])
    if "$or" in clause:
        return any(_match_clause(meta, c) for c in clause["$or"])
    for k, v in clause.items():
        if isinstance(v, dict):
            for op, operand in v.items():
                got = meta.get(k)
                if op == "$gte":
                    if not (isinstance(got, (int, float)) and got >= operand):
                        return False
                elif op == "$lte":
                    if not (isinstance(got, (int, float)) and got <= operand):
                        return False
                elif op == "$gt":
                    if not (isinstance(got, (int, float)) and got > operand):
                        return False
                elif op == "$lt":
                    if not (isinstance(got, (int, float)) and got < operand):
                        return False
                elif op == "$ne":
                    if got == operand:
                        return False
                else:
                    return False
        else:
            if meta.get(k) != v:
                return False
    return True


@dataclass
class FakeStore:
    rows: dict[str, _Row] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.rows)

    def upsert(self, ids, documents, metadatas) -> None:
        for i, doc, meta in zip(ids, documents, metadatas, strict=False):
            self.rows[i] = _Row(id=i, document=doc, metadata=dict(meta))

    def query(self, query_texts, n_results, where=None):
        results = list(self.rows.values())
        if where:
            results = [r for r in results if _match_clause(r.metadata, where)]
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
            results = [r for r in results if _match_clause(r.metadata, where)]
        results = results[:limit]
        return {
            "ids": [r.id for r in results],
            "documents": [r.document for r in results],
            "metadatas": [r.metadata for r in results],
        }

    def delete(self, ids) -> None:
        for i in ids:
            self.rows.pop(i, None)

    def get_all_ids(self) -> list[str]:
        return list(self.rows.keys())

    def get_by_ids(self, ids, include=None):
        rows = [self.rows[i] for i in ids if i in self.rows]
        return {
            "ids": [r.id for r in rows],
            "documents": [r.document for r in rows],
            "metadatas": [r.metadata for r in rows],
        }

    def update_metadatas(self, ids, metadatas) -> None:
        for i, meta in zip(ids, metadatas, strict=False):
            if i in self.rows:
                self.rows[i].metadata = dict(meta)


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

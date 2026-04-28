# @wbx-modified copilot-b1c4 | 2026-04-27 19:30 MTN | v1.2 | structured envelope (rank/distance/type/source/domain/confidence/text) | prev: copilot-c4a1@2026-04-23
"""recall — semantic search across all indexed memory.

Public surface:
  - recall(query, n, type) -> str  (back-compat string for legacy callers)
  - _recall_structured(query, n, type) -> dict {result, results}  (HTTP envelope)
"""

from __future__ import annotations

from ..config import Config
from ..state import compact_checkpoint, staleness_check
from ..store import get_store

_VALID_TYPES = {
    "all",
    "reasoning",
    "anti_pattern",
    "reflection",
    "observation",
    "document",
    "checkpoint",
}


def _recall_rows(query: str, n: int, type: str) -> list[dict]:
    """Run query, return structured rows. Pinned schema:
    rank, distance, type, source, domain, confidence, text.
    """
    if type not in _VALID_TYPES:
        return []
    store = get_store()
    n = min(max(n, 1), 20)
    count = store.count()
    if count == 0:
        return []
    where_filter = {"type": type} if type != "all" else None
    n = min(n, count)
    res = store.query(query_texts=[query], n_results=n, where=where_filter)
    rows: list[dict] = []
    docs = res["documents"][0] if res.get("documents") else []
    metas = res["metadatas"][0] if res.get("metadatas") else []
    dists = res["distances"][0] if res.get("distances") else [None] * len(docs)
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists, strict=False)):
        rows.append(
            {
                "rank": i + 1,
                "distance": float(dist) if dist is not None else None,
                "type": meta.get("type", "document"),
                "source": meta.get("source", "unknown"),
                "domain": meta.get("domain", "") or None,
                "confidence": meta.get("confidence"),
                "text": doc,
            }
        )
    return rows


def _format_recall_string(rows: list[dict]) -> str:
    """Render rows in the legacy marker-line grammar.

    Marker is INTENTIONALLY MINIMAL: `distance | type` only. Domain and
    confidence live in the structured `results[]` array; gateway parsers
    expect `type` to be the last field before the closing `---`.
    """
    if not rows:
        return "No results found."
    out = []
    for r in rows:
        parts = [f"Result {r['rank']}"]
        if r["distance"] is not None:
            parts.append(f"distance: {r['distance']:.3f}")
        parts.append(f"type: {r['type']}")
        out.append(f"--- {' | '.join(parts)} ---\nSource: {r['source']}\n{r['text']}\n")
    return "\n".join(out)


def _recall_structured(
    query: str, n: int = 5, type: str = "all", config: Config | None = None
) -> dict:
    """Pinned envelope for HTTP /tool/recall: {result, results}."""
    cfg = config or _default_config()
    if type not in _VALID_TYPES:
        msg = f"Invalid type '{type}'. Must be one of: {', '.join(sorted(_VALID_TYPES))}"
        return {"result": msg, "results": [], "error": msg}
    store = get_store()
    if store.count() == 0:
        return {"result": "Memory is empty. Run 'reindex' first.", "results": []}
    rows = _recall_rows(query, n, type)
    body = _format_recall_string(rows)
    body += compact_checkpoint(store)
    body += staleness_check(cfg.stale_minutes)
    return {"result": body, "results": rows}


def recall(query: str, n: int = 5, type: str = "all", config: Config | None = None) -> str:
    """Semantic search across all indexed memory.

    Args:
        query: What to search for (natural language).
        n: Number of results (default 5, max 20).
        type: Filter — all, reasoning, anti_pattern, reflection, observation, document, checkpoint.
        config: Runtime config. If None, uses module default.
    """
    payload = _recall_structured(query, n=n, type=type, config=config)
    return payload["result"]


# Lazy default so modules can be imported without env being set (tests).
_cfg: Config | None = None


def _default_config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config

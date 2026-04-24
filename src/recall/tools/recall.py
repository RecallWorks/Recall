# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | recall tool — semantic search across indexed memory | prev: NEW
"""recall — semantic search across all indexed memory."""

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


def recall(query: str, n: int = 5, type: str = "all", config: Config | None = None) -> str:
    """Semantic search across all indexed memory.

    Args:
        query: What to search for (natural language).
        n: Number of results (default 5, max 20).
        type: Filter — all, reasoning, anti_pattern, reflection, observation, document, checkpoint.
        config: Runtime config. If None, uses module default.
    """
    cfg = config or _default_config()
    store = get_store()
    if type not in _VALID_TYPES:
        return f"Invalid type '{type}'. Must be one of: {', '.join(sorted(_VALID_TYPES))}"
    n = min(max(n, 1), 20)
    count = store.count()
    if count == 0:
        return "Memory is empty. Run 'reindex' first."
    where_filter = {"type": type} if type != "all" else None
    n = min(n, count)
    results = store.query(query_texts=[query], n_results=n, where=where_filter)
    output: list[str] = []
    docs = results["documents"][0] if results.get("documents") else []
    metas = results["metadatas"][0] if results.get("metadatas") else []
    dists = results["distances"][0] if results.get("distances") else [None] * len(docs)
    for i, (doc, meta) in enumerate(zip(docs, metas, strict=False)):
        source = meta.get("source", "unknown")
        art_type = meta.get("type", "document")
        domain = meta.get("domain", "")
        confidence = meta.get("confidence")
        dist = dists[i] if i < len(dists) else None
        header = [f"Result {i + 1}"]
        if dist is not None:
            header.append(f"distance: {dist:.3f}")
        header.append(f"type: {art_type}")
        if domain:
            header.append(f"domain: {domain}")
        if confidence is not None:
            header.append(f"confidence: {confidence}")
        output.append(f"--- {' | '.join(header)} ---\nSource: {source}\n{doc}\n")
    result = "\n".join(output) if output else "No results found."
    result += compact_checkpoint(store)
    result += staleness_check(cfg.stale_minutes)
    return result


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

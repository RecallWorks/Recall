# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | memory_stats + forget — forget archives via tombstone metadata; physical delete only happens via explicit purge tool (delete=archive guardrail) | prev: NEW
"""memory_stats / forget — read store metadata + soft-archive a source.

Per the founder's binary guardrail (delete = archive), `forget` does NOT
hard-delete chunks. Instead it tags them as archived so they're filtered
from default queries. A separate `purge` tool (not in v0.1) would be the
only way to physically remove rows.
"""
from __future__ import annotations

import json
from datetime import datetime

from ..config import Config
from ..store import get_store

_cfg: Config | None = None


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config


def _config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def memory_stats() -> str:
    """Show memory store statistics."""
    cfg = _config()
    store = get_store()
    count = store.count()
    if count == 0:
        return "Memory store is empty. Run 'reindex' to populate."
    sample = store.get(limit=min(count, 500), include=["metadatas"])
    sources = set()
    types: dict[str, int] = {}
    for meta in sample["metadatas"]:
        sources.add(meta.get("source", "unknown"))
        t = meta.get("type", "document")
        types[t] = types.get(t, 0) + 1
    lines = [
        f"Total chunks: {count}",
        f"Unique sources: {len(sources)}",
        f"Types: {json.dumps(types)}",
        f"Store path: {cfg.store_dir}",
        "",
        "Sources (sample):",
    ]
    for s in sorted(sources)[:20]:
        lines.append(f"  - {s}")
    if len(sources) > 20:
        lines.append(f"  ... and {len(sources) - 20} more")
    return "\n".join(lines)


def forget(source: str) -> str:
    """Archive (soft-delete) all chunks from a specific source.

    Tags chunks with archived=true + archived_at=ISO; default queries can
    filter them out. Per delete=archive guardrail, no physical delete.

    Args:
        source: The source label to archive (exact match).
    """
    store = get_store()
    results = store.get(where={"source": source}, limit=10000, include=["documents", "metadatas"])
    if not results["ids"]:
        return f"No chunks found with source: {source}"
    archived_at = datetime.now().isoformat()
    new_metas: list[dict] = []
    for meta in results["metadatas"]:
        m = dict(meta)
        m["archived"] = True
        m["archived_at"] = archived_at
        new_metas.append(m)
    store.upsert(
        ids=results["ids"],
        documents=results["documents"],
        metadatas=new_metas,
    )
    return f"Archived {len(results['ids'])} chunks from source: {source} (delete=archive guardrail)"

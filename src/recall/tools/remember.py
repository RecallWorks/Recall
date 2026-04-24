# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | remember tool | prev: NEW
"""remember — store an observation for future recall."""
from __future__ import annotations

import hashlib
from datetime import datetime

from ..artifacts import persist_artifact
from ..config import Config
from ..snapshot import maybe_auto_snapshot
from ..state import staleness_check
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


def remember(content: str, source: str = "agent-observation", tags: str = "") -> str:
    """Store a memory/observation for future recall.

    Args:
        content: The text to remember.
        source: Label for the source.
        tags: Comma-separated tags.
    """
    cfg = _config()
    store = get_store()
    chunk_id = hashlib.sha256(
        f"{source}:{datetime.now().isoformat()}:{content[:50]}".encode()
    ).hexdigest()[:16]
    metadata = {
        "source": source,
        "chunk_index": 0,
        "indexed_at": datetime.now().isoformat(),
        "type": "observation",
    }
    if tags:
        metadata["tags"] = tags
    store.upsert(ids=[chunk_id], documents=[content], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "observations",
        f"{source}_{chunk_id}",
        f"# Observation: {source}\n\nTags: {tags}\nStored: {metadata['indexed_at']}\n\n{content}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return f"Stored. ID: {chunk_id}, source: {source}" + staleness_check(cfg.stale_minutes)

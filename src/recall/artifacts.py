# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | artifact persistence | prev: NEW
"""Artifact persistence — write tool outputs to disk as .md files.

Why: ChromaDB lives on ephemeral local disk. Source-of-truth artifacts
(observations, reasoning, anti-patterns, checkpoints, reflections) must
survive container restarts. They're written here and re-indexed on startup.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger("recall.artifacts")


def persist_artifact(artifacts_dir: str, art_type: str, filename: str, content: str) -> str:
    """Write an artifact to durable storage. Returns filepath written, or '' on failure."""
    type_dir = os.path.join(artifacts_dir, art_type)
    os.makedirs(type_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
    filepath = os.path.join(type_dir, f"{safe_name}.md")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        log.info("Persisted %s artifact: %s", art_type, filepath)
        return filepath
    except OSError as e:
        log.error("Failed to persist artifact %s: %s", filepath, e)
        return ""

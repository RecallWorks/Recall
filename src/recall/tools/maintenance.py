# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | maintenance + snapshot_index | prev: NEW
"""maintenance — git pull + reindex + warm query + snapshot.
snapshot_index — explicit durable copy of the live store."""
from __future__ import annotations

import glob
import logging
import os
import subprocess

from ..chunking import index_file as _index_file_impl
from ..config import Config
from ..git_sync import resolve_index_paths
from ..snapshot import snapshot
from ..store import get_store

log = logging.getLogger("recall.maintenance")

_cfg: Config | None = None


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config


def _config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def maintenance(pull: bool = True) -> str:
    """Run maintenance cycle: git pull + reindex + warm query + snapshot.

    Called by an external scheduler (timer function, cron) to keep the brain fresh.

    Args:
        pull: Whether to git pull before reindex (default True).
    """
    cfg = _config()
    store = get_store()
    results: list[str] = []

    if pull and cfg.git_repo_url:
        try:
            proc = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=cfg.repo_dir,
                capture_output=True, text=True,
                timeout=60,
            )
            results.append(f"Git pull: {proc.stdout.strip() or proc.stderr.strip()}")
        except Exception as e:
            results.append(f"Git pull failed: {e}")

    indexed = 0
    files_processed = 0
    for index_path in resolve_index_paths(cfg.repo_dir, cfg.index_dirs, cfg.artifacts_dir):
        for ext in cfg.file_extensions:
            for filepath in glob.glob(os.path.join(index_path, "**", f"*{ext}"), recursive=True):
                if os.path.isfile(filepath):
                    n = _index_file_impl(store, filepath, cfg.chunk_size, cfg.chunk_overlap)
                    if n > 0:
                        files_processed += 1
                        indexed += n
    results.append(f"Reindex: {indexed} chunks from {files_processed} files")

    if store.count() > 0:
        store.query(query_texts=["warm"], n_results=1)
        results.append("Warm query: OK")

    try:
        results.append(snapshot(cfg.store_dir, cfg.prebuilt_dir))
    except Exception as e:
        log.error("Snapshot after maintenance failed: %s", e)
        results.append(f"Snapshot failed: {e}")

    log.info("Maintenance complete: %s", "; ".join(results))
    return " | ".join(results)


def snapshot_index() -> str:
    """Copy the live store_dir to prebuilt_dir atomically.

    The boot script copies prebuilt_dir -> store_dir on every restart, so this
    is what keeps writes durable across container restarts.
    """
    cfg = _config()
    return snapshot(cfg.store_dir, cfg.prebuilt_dir)

# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | reindex + index_file tools | prev: NEW
"""reindex / index_file — populate the store from disk."""
from __future__ import annotations

import glob
import os

from ..chunking import index_file as _index_file_impl
from ..config import Config
from ..git_sync import resolve_index_paths
from ..snapshot import maybe_auto_snapshot
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


def reindex(path: str = "") -> str:
    """Re-scan and index source files. Empty path = all configured paths.

    Args:
        path: Optional specific file or directory to index.
    """
    cfg = _config()
    store = get_store()
    indexed = 0
    files_processed = 0

    targets: list[str] = []
    if path and os.path.exists(path):
        if os.path.isfile(path):
            targets = [path]
        elif os.path.isdir(path):
            for ext in cfg.file_extensions:
                targets.extend(glob.glob(os.path.join(path, "**", f"*{ext}"), recursive=True))
    else:
        for index_path in resolve_index_paths(cfg.repo_dir, cfg.index_dirs, cfg.artifacts_dir):
            for ext in cfg.file_extensions:
                targets.extend(glob.glob(os.path.join(index_path, "**", f"*{ext}"), recursive=True))

    for filepath in targets:
        if os.path.isfile(filepath):
            n = _index_file_impl(store, filepath, cfg.chunk_size, cfg.chunk_overlap)
            if n > 0:
                files_processed += 1
                indexed += n

    if indexed > 0:
        maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return f"Indexed {indexed} chunks from {files_processed} files."


def index_file(filepath: str) -> str:
    """Index a single file.

    Args:
        filepath: Path to the file to index.
    """
    cfg = _config()
    store = get_store()
    if not os.path.isfile(filepath):
        return f"File not found: {filepath}"
    n = _index_file_impl(store, filepath, cfg.chunk_size, cfg.chunk_overlap)
    if n > 0:
        maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return f"Indexed {n} chunks from {filepath}"

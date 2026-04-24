# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | snapshot + auto-snapshot | prev: NEW
"""Snapshot the live ChromaDB store to a durable location.

The store lives on ephemeral local disk; without snapshots, every container
restart loses chunks added since the last CI-built prebuilt index. The boot
script copies prebuilt_dir -> store_dir so restarts come up whole.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile

from .state import S
from .store import get_store, is_ready

log = logging.getLogger("recall.snapshot")


def snapshot(store_dir: str, prebuilt_dir: str) -> str:
    """Copy the live store_dir to prebuilt_dir atomically. Returns a status string."""
    if not is_ready():
        return "Snapshot skipped: store not initialized"
    chunks = get_store().count()
    parent = os.path.dirname(prebuilt_dir.rstrip("/")) or "/"
    os.makedirs(parent, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix=".prebuilt-index-tmp-", dir=parent)
    try:
        for fname in os.listdir(store_dir):
            src = os.path.join(store_dir, fname)
            dst = os.path.join(tmp_dir, fname)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
        backup_dir = prebuilt_dir.rstrip("/") + ".bak"
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)
        if os.path.isdir(prebuilt_dir):
            os.rename(prebuilt_dir, backup_dir)
        os.rename(tmp_dir, prebuilt_dir)
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)
        log.info("Snapshot OK: %d chunks -> %s", chunks, prebuilt_dir)
        return f"Snapshot: {chunks} chunks -> {prebuilt_dir}"
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def maybe_auto_snapshot(store_dir: str, prebuilt_dir: str, every: int) -> None:
    """Increment write counter; snapshot if threshold reached. Best-effort.

    Write tools call this after every successful upsert. Failures are logged
    but never raised — the underlying tool call must succeed even if the
    snapshot can't be written.
    """
    if every <= 0:
        return
    S.writes_since_snapshot += 1
    if S.writes_since_snapshot < every:
        return
    try:
        result = snapshot(store_dir, prebuilt_dir)
        log.info(
            "Auto-snapshot fired (after %d writes): %s",
            S.writes_since_snapshot,
            result,
        )
        S.writes_since_snapshot = 0
    except Exception as e:
        log.error("Auto-snapshot failed (will retry next threshold): %s", e)

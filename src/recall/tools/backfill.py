# @wbx-modified copilot-b1c4 | 2026-04-27 19:30 MTN | v1.0 | one-shot migration: backfill indexed_at_epoch | prev: NEW
"""backfill_epoch — add indexed_at_epoch (numeric) to chunks that only have
indexed_at (ISO string). Idempotent. Paginate by id-order.

Required because ChromaDB rejects $gte on string fields, so since= queries
in recall_filtered need numeric epoch on every chunk.
"""

from __future__ import annotations

import time
from datetime import datetime

from ..store import get_store


def backfill_epoch(start: int = 0, batch_size: int = 2000) -> str:
    """Process one page. Call repeatedly with start += batch_size until 'done'.

    Returns: 'progress: scanned=X fixed=Y skipped=Z next=N total=T' or
             'done: scanned=X fixed=Y skipped=Z failed=F total=T'.

    NOT a delete operation. Uses collection.update(ids, metadatas) to add
    the new field; total chunk count is invariant across the entire run.
    """
    store = get_store()
    # Direct chroma helpers added in store.py: get_all_ids / get_by_ids /
    # update_metadatas. Tools relying on these accept a ChromaStore-like
    # object; tests can supply a fake exposing the same methods.
    if not hasattr(store, "get_all_ids"):
        return "error: store backend does not support backfill (no get_all_ids)"
    all_ids = store.get_all_ids()
    total = len(all_ids)
    if start >= total:
        return f"done: scanned={total} total={total}"
    page_ids = all_ids[start : start + batch_size]
    page = store.get_by_ids(page_ids, include=["metadatas"])
    update_ids: list[str] = []
    update_metas: list[dict] = []
    skipped = 0
    failed = 0
    for cid, meta in zip(page["ids"], page["metadatas"], strict=False):
        if not meta:
            skipped += 1
            continue
        ep = meta.get("indexed_at_epoch")
        if isinstance(ep, (int, float)) and ep > 0:
            skipped += 1
            continue
        iso = meta.get("indexed_at")
        try:
            if iso:
                ts = datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp()
            else:
                ts = time.time()
            new_meta = dict(meta)
            new_meta["indexed_at_epoch"] = float(ts)
            update_ids.append(cid)
            update_metas.append(new_meta)
        except Exception:
            failed += 1
            continue
    if update_ids:
        store.update_metadatas(update_ids, update_metas)
    next_start = start + batch_size
    if next_start >= total:
        return (
            f"done: scanned={start + len(page_ids)} fixed={len(update_ids)} "
            f"skipped={skipped} failed={failed} total={total}"
        )
    return (
        f"progress: scanned={start + len(page_ids)} fixed={len(update_ids)} "
        f"skipped={skipped} failed={failed} next={next_start} total={total}"
    )

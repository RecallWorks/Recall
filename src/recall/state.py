# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | shared mutable state | prev: NEW
"""Shared mutable state used across tools.

Holds:
- Checkpoint ring buffer (recent in-memory cache before re-querying store).
- Last-checkpoint timestamp (for staleness warnings).
- Auto-snapshot write counter.

This module is intentionally tiny so tools can `from recall.state import S`
without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class State:
    checkpoint_ring: list[dict] = field(default_factory=list)
    last_checkpoint_ts: datetime | None = None
    writes_since_snapshot: int = 0


# Module-level singleton. Tests reset by reassigning fields.
S = State()


def staleness_check(stale_minutes: int) -> str:
    """Return a warning suffix if the last checkpoint is stale (or missing)."""
    if S.last_checkpoint_ts is None:
        return (
            "\n\n\u26a0\ufe0f NO CHECKPOINT EXISTS \u2014 your working state is not "
            "saved. Call checkpoint() now."
        )
    age = (datetime.now() - S.last_checkpoint_ts).total_seconds() / 60
    if age >= stale_minutes:
        return (
            f"\n\n\u26a0\ufe0f CHECKPOINT STALE ({age:.0f} min old) \u2014 call "
            f"checkpoint() to save current context."
        )
    return ""


def compact_checkpoint(store) -> str:
    """Return the latest checkpoint document, formatted as an active-context block."""
    if S.checkpoint_ring:
        latest = S.checkpoint_ring[-1]
        return f"\n\n\U0001f4cd ACTIVE CONTEXT (checkpoint {latest['ts']}):\n{latest['document']}\n"
    if store.count() > 0:
        cp = store.query(
            query_texts=["checkpoint current state intent"],
            n_results=1,
            where={"type": "checkpoint"},
        )
        if cp["documents"] and cp["documents"][0]:
            return (
                f"\n\n\U0001f4cd ACTIVE CONTEXT (from persistent store):\n{cp['documents'][0][0]}\n"
            )
    return ""

# @wbx-modified copilot-a3f7 | 2026-04-30 00:58 MTN | v1.3 | added coordinate.* (claim/release/who_has/claims/handoff/pulse_others) for multi-agent wedge | prev: copilot-b1c4@2026-04-27 19:30 MTN
"""Tool modules. Each module exposes a single public callable named after
the tool, plus an optional `register(mcp)` helper used by mcp_sse transport.

The HTTP transport reads from TOOL_REGISTRY directly.
"""

from __future__ import annotations

from . import answer as _answer
from . import backfill as _backfill
from . import checkpoint as _checkpoint
from . import coordinate as _coordinate
from . import maintenance as _maintenance
from . import recall as _recall
from . import recall_filtered as _recall_filtered
from . import reflect as _reflect
from . import reindex as _reindex
from . import remember as _remember
from . import stats as _stats

TOOL_REGISTRY = {
    "recall": _recall.recall,
    "recall_filtered": _recall_filtered.recall_filtered,
    "answer": _answer.answer,
    "remember": _remember.remember,
    "reindex": _reindex.reindex,
    "index_file": _reindex.index_file,
    "memory_stats": _stats.memory_stats,
    "forget": _stats.forget,
    "reflect": _reflect.reflect,
    "anti_pattern": _reflect.anti_pattern,
    "session_close": _reflect.session_close,
    "checkpoint": _checkpoint.checkpoint,
    "pulse": _checkpoint.pulse,
    "maintenance": _maintenance.maintenance,
    "snapshot_index": _maintenance.snapshot_index,
    "backfill_epoch": _backfill.backfill_epoch,
    # Multi-agent coordination (v0.5.0 wedge) ----------------------------
    "claim": _coordinate.claim,
    "release": _coordinate.release,
    "who_has": _coordinate.who_has,
    "claims": _coordinate.claims,
    "handoff": _coordinate.handoff,
    "pulse_others": _coordinate.pulse_others,
}


WRITE_TOOLS = {
    "remember",
    "reindex",
    "index_file",
    "forget",
    "reflect",
    "anti_pattern",
    "session_close",
    "checkpoint",
    "maintenance",
    "snapshot_index",
    "backfill_epoch",
    "claim",
    "release",
    "handoff",
}

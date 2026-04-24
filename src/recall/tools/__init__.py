# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — tool registry | prev: NEW
"""Tool modules. Each module exposes a single public callable named after
the tool, plus an optional `register(mcp)` helper used by mcp_sse transport.

The HTTP transport reads from TOOL_REGISTRY directly.
"""
from __future__ import annotations

from . import recall as _recall
from . import remember as _remember
from . import reindex as _reindex
from . import stats as _stats
from . import reflect as _reflect
from . import checkpoint as _checkpoint
from . import maintenance as _maintenance


TOOL_REGISTRY = {
    "recall":         _recall.recall,
    "remember":       _remember.remember,
    "reindex":        _reindex.reindex,
    "index_file":     _reindex.index_file,
    "memory_stats":   _stats.memory_stats,
    "forget":         _stats.forget,
    "reflect":        _reflect.reflect,
    "anti_pattern":   _reflect.anti_pattern,
    "session_close":  _reflect.session_close,
    "checkpoint":     _checkpoint.checkpoint,
    "pulse":          _checkpoint.pulse,
    "maintenance":    _maintenance.maintenance,
    "snapshot_index": _maintenance.snapshot_index,
}


WRITE_TOOLS = {
    "remember", "reindex", "index_file", "forget", "reflect",
    "anti_pattern", "session_close", "checkpoint", "maintenance",
    "snapshot_index",
}

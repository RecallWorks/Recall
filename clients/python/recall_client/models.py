# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | response model matching real envelope | prev: typed Hits
"""Response model for Recall tool calls.

Every Recall tool returns the JSON envelope ``{"result": str, "tool": str, "by": str}``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResponse:
    """Wraps a Recall tool response.

    ``result`` is always the tool's return value coerced to ``str`` by the
    server. For ``recall``/``pulse``/``memory_stats`` it's human-readable
    markdown. For ``remember``/``reflect``/etc it's a status line.
    """

    result: str
    tool: str
    by: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ToolResponse:
        return cls(
            result=str(d.get("result", "")),
            tool=str(d.get("tool", "")),
            by=str(d.get("by", "")),
        )

    def __str__(self) -> str:  # pragma: no cover
        return self.result

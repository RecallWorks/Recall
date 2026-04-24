# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | typed response models | prev: NEW
"""Typed response models for Recall SDK.

Models are dataclasses (no Pydantic dep) for zero-friction install.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hit:
    """A single recall search hit."""

    content: str
    score: float
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Hit:
        return cls(
            content=d.get("content", ""),
            score=float(d.get("score", 0.0)),
            tags=list(d.get("tags", [])),
            metadata=dict(d.get("metadata", {})),
            id=d.get("id"),
        )


@dataclass
class RememberResult:
    """Result of a remember() call."""

    id: str
    artifact_path: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RememberResult:
        return cls(
            id=d.get("id", ""),
            artifact_path=d.get("artifact_path"),
        )


@dataclass
class ToolResult:
    """Generic tool-invocation result for tools without a typed wrapper."""

    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ToolResult:
        return cls(
            ok=bool(d.get("ok", True)),
            data=dict(d) if "ok" not in d else {k: v for k, v in d.items() if k != "ok"},
            error=d.get("error"),
        )

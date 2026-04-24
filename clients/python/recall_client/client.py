# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | sync HTTP client (real contract) | prev: 0.1.0
"""Synchronous Recall client. Mirrors the server's real tool registry."""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import (
    RecallAuthError,
    RecallConnectionError,
    RecallServerError,
    RecallToolError,
)
from .models import ToolResponse


class RecallClient:
    """Synchronous HTTP client for a Recall server.

    Args:
        base_url: Base URL of the Recall server, e.g. ``http://localhost:8787``.
        api_key: API key sent as ``X-API-Key``.
        timeout: Per-request timeout in seconds. Default 30.
        client: Optional pre-configured ``httpx.Client``.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "recall-client-python/0.2.0",
            },
        )

    def __enter__(self) -> RecallClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # ── core dispatch ────────────────────────────────────────────────────

    def call_tool(self, name: str, **kwargs: Any) -> ToolResponse:
        """Invoke any registered tool by name."""
        url = f"{self.base_url}/tool/{name}"
        try:
            resp = self._client.post(url, json=kwargs)
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach {url}: {e}") from e

        if resp.status_code in (401, 403):
            raise RecallAuthError(f"Auth failed ({resp.status_code}): {resp.text}")
        if resp.status_code >= 500:
            raise RecallServerError(
                f"Server error {resp.status_code}: {resp.text}", resp.status_code
            )
        if resp.status_code >= 400:
            raise RecallToolError(name, f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if isinstance(data, dict) and "error" in data and data.get("error"):
            raise RecallToolError(name, str(data["error"]))
        if not isinstance(data, dict):
            raise RecallToolError(name, f"unexpected response shape: {data!r}")
        return ToolResponse.from_dict(data)

    # ── typed wrappers (exact server signatures) ─────────────────────────

    def remember(
        self, content: str, source: str = "agent-observation", tags: str = ""
    ) -> ToolResponse:
        """Store a memory.

        Args:
            content: The text to remember.
            source: Origin label (default ``agent-observation``).
            tags: Comma-separated tag string (e.g. ``"pref,ui"``).
        """
        return self.call_tool("remember", content=content, source=source, tags=tags)

    def recall(self, query: str, n: int = 5, type: str = "all") -> ToolResponse:
        """Semantic recall.

        Args:
            query: What to search for.
            n: Number of hits to return (default 5).
            type: Filter (``all`` | ``observation`` | ``reflection`` | ``checkpoint``).
        """
        return self.call_tool("recall", query=query, n=n, type=type)

    def reflect(
        self,
        domain: str,
        hypothesis: str,
        reasoning: str,
        result: str,
        revised_belief: str,
        next_time: str,
        confidence: float = 0.7,
        session: str = "",
    ) -> ToolResponse:
        """Persist a structured reasoning artifact."""
        return self.call_tool(
            "reflect",
            domain=domain,
            hypothesis=hypothesis,
            reasoning=reasoning,
            result=result,
            revised_belief=revised_belief,
            next_time=next_time,
            confidence=confidence,
            session=session,
        )

    def anti_pattern(
        self,
        domain: str,
        temptation: str,
        why_wrong: str,
        signature: str,
        instead: str,
        session: str = "",
    ) -> ToolResponse:
        """Record a 'looks right but isn't' pattern."""
        return self.call_tool(
            "anti_pattern",
            domain=domain,
            temptation=temptation,
            why_wrong=why_wrong,
            signature=signature,
            instead=instead,
            session=session,
        )

    def session_close(
        self,
        session_id: str,
        reasoning_changed: str,
        do_differently: str,
        still_uncertain: str,
        temptations: str,
    ) -> ToolResponse:
        """End-of-session reflection."""
        return self.call_tool(
            "session_close",
            session_id=session_id,
            reasoning_changed=reasoning_changed,
            do_differently=do_differently,
            still_uncertain=still_uncertain,
            temptations=temptations,
        )

    def checkpoint(
        self,
        intent: str,
        established: str,
        pursuing: str,
        open_questions: str,
        session: str = "",
        domain: str = "",
    ) -> ToolResponse:
        """Snapshot current working state."""
        return self.call_tool(
            "checkpoint",
            intent=intent,
            established=established,
            pursuing=pursuing,
            open_questions=open_questions,
            session=session,
            domain=domain,
        )

    def pulse(self, domain: str = "", include_reasoning: bool = True) -> ToolResponse:
        """Get current orientation (last checkpoint, recent reasoning)."""
        return self.call_tool("pulse", domain=domain, include_reasoning=include_reasoning)

    def memory_stats(self) -> ToolResponse:
        """Aggregate counts across the store."""
        return self.call_tool("memory_stats")

    def forget(self, source: str) -> ToolResponse:
        """Soft-archive all chunks matching ``source``.

        NOTE: ``source`` is the tag/source label, NOT a chunk id. The server
        marks matching chunks ``archived=true`` rather than deleting them.
        """
        return self.call_tool("forget", source=source)

    def reindex(self, path: str = "") -> ToolResponse:
        """Re-index a path (or the whole corpus if empty)."""
        return self.call_tool("reindex", path=path)

    def index_file(self, filepath: str) -> ToolResponse:
        """Index a single file."""
        return self.call_tool("index_file", filepath=filepath)

    def maintenance(self, pull: bool = True) -> ToolResponse:
        """Run maintenance (default: pull latest corpus + reindex)."""
        return self.call_tool("maintenance", pull=pull)

    def snapshot_index(self) -> ToolResponse:
        """Snapshot the current index to the prebuilt directory."""
        return self.call_tool("snapshot_index")

    # ── plain HTTP endpoints (no auth) ────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """GET /health — does not require auth."""
        try:
            resp = self._client.get(f"{self.base_url}/health")
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach health: {e}") from e
        if resp.status_code != 200:
            raise RecallServerError(
                f"Health failed: {resp.status_code}", resp.status_code
            )
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}

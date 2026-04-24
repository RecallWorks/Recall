# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | sync HTTP client | prev: NEW
"""Synchronous Recall client.

Uses httpx.Client. Thread-safe. Use as a context manager or call ``close()``.
"""

from __future__ import annotations

from typing import Any

import httpx

from .exceptions import (
    RecallAuthError,
    RecallConnectionError,
    RecallServerError,
    RecallToolError,
)
from .models import Hit, RememberResult, ToolResult


class RecallClient:
    """Synchronous HTTP client for a Recall server.

    Args:
        base_url: Base URL of the Recall server, e.g. ``http://localhost:8787``.
        api_key: API key sent as ``Authorization: Bearer <key>``.
        timeout: Per-request timeout in seconds. Default 30.
        client: Optional pre-configured ``httpx.Client``. If provided,
            ``base_url`` and ``api_key`` are still used to build request URLs
            and headers, but the underlying transport is yours.
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
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "recall-client-python/0.1.0",
            },
        )

    def __enter__(self) -> RecallClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client (only if we own it)."""
        if self._owns_client:
            self._client.close()

    # ── core tool dispatch ────────────────────────────────────────────────

    def call_tool(self, name: str, **payload: Any) -> dict[str, Any]:
        """Invoke any tool by name. Returns the raw JSON response."""
        url = f"{self.base_url}/tool/{name}"
        try:
            resp = self._client.post(url, json=payload)
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach {url}: {e}") from e

        if resp.status_code in (401, 403):
            raise RecallAuthError(f"Auth failed ({resp.status_code}): {resp.text}")
        if resp.status_code >= 500:
            raise RecallServerError(
                f"Server error {resp.status_code}: {resp.text}",
                resp.status_code,
            )
        if resp.status_code >= 400:
            raise RecallToolError(name, f"HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if isinstance(data, dict) and data.get("error"):
            raise RecallToolError(name, str(data["error"]))
        return data if isinstance(data, dict) else {"result": data}

    # ── typed convenience wrappers ────────────────────────────────────────

    def remember(
        self,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RememberResult:
        """Store a memory. Returns the assigned id."""
        payload: dict[str, Any] = {"content": content}
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata
        result = self.call_tool("remember", **payload)
        return RememberResult.from_dict(result)

    def recall(
        self,
        query: str,
        limit: int = 5,
        tags: list[str] | None = None,
    ) -> list[Hit]:
        """Search memories semantically. Returns ranked hits."""
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if tags:
            payload["tags"] = tags
        result = self.call_tool("recall", **payload)
        hits = result.get("hits", result.get("results", []))
        return [Hit.from_dict(h) for h in hits]

    def reflect(self, summary: str, tags: list[str] | None = None) -> ToolResult:
        """Persist a reflection / lesson learned."""
        payload: dict[str, Any] = {"summary": summary}
        if tags:
            payload["tags"] = tags
        return ToolResult.from_dict(self.call_tool("reflect", **payload))

    def checkpoint(
        self,
        session: str,
        established: str,
        intent: str,
        pursuing: str,
        summary: str,
        open_questions: list[str] | None = None,
    ) -> ToolResult:
        """Snapshot the current session state."""
        return ToolResult.from_dict(
            self.call_tool(
                "checkpoint",
                session=session,
                established=established,
                intent=intent,
                pursuing=pursuing,
                summary=summary,
                open_questions=open_questions or [],
            )
        )

    def pulse(self) -> dict[str, Any]:
        """Get current server health + active sessions."""
        return self.call_tool("pulse")

    def memory_stats(self) -> dict[str, Any]:
        """Get aggregate counts (chunks, sessions, artifacts)."""
        return self.call_tool("memory_stats")

    def forget(self, id: str, source: str = "user-request") -> ToolResult:
        """Soft-archive a memory by id. Source defaults to 'user-request'."""
        return ToolResult.from_dict(self.call_tool("forget", id=id, source=source))

    def health(self) -> dict[str, Any]:
        """Plain GET /health — does not require a tool path."""
        try:
            resp = self._client.get(f"{self.base_url}/health")
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach health: {e}") from e
        if resp.status_code != 200:
            raise RecallServerError(f"Health failed: {resp.status_code}", resp.status_code)
        return resp.json()

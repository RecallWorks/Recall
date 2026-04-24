# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | async HTTP client | prev: NEW
"""Asynchronous Recall client. Mirrors RecallClient API surface."""

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


class AsyncRecallClient:
    """Async HTTP client for a Recall server. Use as an async context manager."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "recall-client-python/0.1.0",
            },
        )

    async def __aenter__(self) -> AsyncRecallClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def call_tool(self, name: str, **payload: Any) -> dict[str, Any]:
        url = f"{self.base_url}/tool/{name}"
        try:
            resp = await self._client.post(url, json=payload)
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

    async def remember(
        self,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RememberResult:
        payload: dict[str, Any] = {"content": content}
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata
        return RememberResult.from_dict(await self.call_tool("remember", **payload))

    async def recall(
        self, query: str, limit: int = 5, tags: list[str] | None = None
    ) -> list[Hit]:
        payload: dict[str, Any] = {"query": query, "limit": limit}
        if tags:
            payload["tags"] = tags
        result = await self.call_tool("recall", **payload)
        hits = result.get("hits", result.get("results", []))
        return [Hit.from_dict(h) for h in hits]

    async def reflect(self, summary: str, tags: list[str] | None = None) -> ToolResult:
        payload: dict[str, Any] = {"summary": summary}
        if tags:
            payload["tags"] = tags
        return ToolResult.from_dict(await self.call_tool("reflect", **payload))

    async def checkpoint(
        self,
        session: str,
        established: str,
        intent: str,
        pursuing: str,
        summary: str,
        open_questions: list[str] | None = None,
    ) -> ToolResult:
        return ToolResult.from_dict(
            await self.call_tool(
                "checkpoint",
                session=session,
                established=established,
                intent=intent,
                pursuing=pursuing,
                summary=summary,
                open_questions=open_questions or [],
            )
        )

    async def pulse(self) -> dict[str, Any]:
        return await self.call_tool("pulse")

    async def memory_stats(self) -> dict[str, Any]:
        return await self.call_tool("memory_stats")

    async def forget(self, id: str, source: str = "user-request") -> ToolResult:
        return ToolResult.from_dict(await self.call_tool("forget", id=id, source=source))

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self._client.get(f"{self.base_url}/health")
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach health: {e}") from e
        if resp.status_code != 200:
            raise RecallServerError(f"Health failed: {resp.status_code}", resp.status_code)
        return resp.json()

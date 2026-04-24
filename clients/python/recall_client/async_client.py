# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | async client matching real contract | prev: 0.1.0
"""Asynchronous Recall client. Mirrors RecallClient surface."""

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


class AsyncRecallClient:
    """Async HTTP client for a Recall server."""

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
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "recall-client-python/0.2.0",
            },
        )

    async def __aenter__(self) -> AsyncRecallClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def call_tool(self, name: str, **kwargs: Any) -> ToolResponse:
        url = f"{self.base_url}/tool/{name}"
        try:
            resp = await self._client.post(url, json=kwargs)
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

    async def remember(
        self, content: str, source: str = "agent-observation", tags: str = ""
    ) -> ToolResponse:
        return await self.call_tool("remember", content=content, source=source, tags=tags)

    async def recall(self, query: str, n: int = 5, type: str = "all") -> ToolResponse:
        return await self.call_tool("recall", query=query, n=n, type=type)

    async def reflect(
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
        return await self.call_tool(
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

    async def anti_pattern(
        self,
        domain: str,
        temptation: str,
        why_wrong: str,
        signature: str,
        instead: str,
        session: str = "",
    ) -> ToolResponse:
        return await self.call_tool(
            "anti_pattern",
            domain=domain,
            temptation=temptation,
            why_wrong=why_wrong,
            signature=signature,
            instead=instead,
            session=session,
        )

    async def session_close(
        self,
        session_id: str,
        reasoning_changed: str,
        do_differently: str,
        still_uncertain: str,
        temptations: str,
    ) -> ToolResponse:
        return await self.call_tool(
            "session_close",
            session_id=session_id,
            reasoning_changed=reasoning_changed,
            do_differently=do_differently,
            still_uncertain=still_uncertain,
            temptations=temptations,
        )

    async def checkpoint(
        self,
        intent: str,
        established: str,
        pursuing: str,
        open_questions: str,
        session: str = "",
        domain: str = "",
    ) -> ToolResponse:
        return await self.call_tool(
            "checkpoint",
            intent=intent,
            established=established,
            pursuing=pursuing,
            open_questions=open_questions,
            session=session,
            domain=domain,
        )

    async def pulse(
        self, domain: str = "", include_reasoning: bool = True
    ) -> ToolResponse:
        return await self.call_tool(
            "pulse", domain=domain, include_reasoning=include_reasoning
        )

    async def memory_stats(self) -> ToolResponse:
        return await self.call_tool("memory_stats")

    async def forget(self, source: str) -> ToolResponse:
        return await self.call_tool("forget", source=source)

    async def reindex(self, path: str = "") -> ToolResponse:
        return await self.call_tool("reindex", path=path)

    async def index_file(self, filepath: str) -> ToolResponse:
        return await self.call_tool("index_file", filepath=filepath)

    async def maintenance(self, pull: bool = True) -> ToolResponse:
        return await self.call_tool("maintenance", pull=pull)

    async def snapshot_index(self) -> ToolResponse:
        return await self.call_tool("snapshot_index")

    async def health(self) -> dict[str, Any]:
        try:
            resp = await self._client.get(f"{self.base_url}/health")
        except httpx.RequestError as e:
            raise RecallConnectionError(f"Cannot reach health: {e}") from e
        if resp.status_code != 200:
            raise RecallServerError(
                f"Health failed: {resp.status_code}", resp.status_code
            )
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}

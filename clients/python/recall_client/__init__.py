# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | Python SDK package init | prev: NEW
"""recall_client — official Python SDK for Recall memory server.

Quick start:

    from recall_client import RecallClient

    client = RecallClient("http://localhost:8787", api_key="changeme")
    client.remember("first memory", tags=["hello"])
    hits = client.recall("hello", limit=5)
    for h in hits:
        print(h.content, h.score)

Async usage:

    from recall_client import AsyncRecallClient

    async with AsyncRecallClient("http://localhost:8787", api_key="changeme") as c:
        await c.remember("async memory")
        hits = await c.recall("memory")
"""

from .async_client import AsyncRecallClient
from .client import RecallClient
from .exceptions import (
    RecallAuthError,
    RecallConnectionError,
    RecallError,
    RecallServerError,
    RecallToolError,
)
from .models import Hit, RememberResult, ToolResult

__version__ = "0.1.0"
__all__ = [
    "AsyncRecallClient",
    "Hit",
    "RecallAuthError",
    "RecallClient",
    "RecallConnectionError",
    "RecallError",
    "RecallServerError",
    "RecallToolError",
    "RememberResult",
    "ToolResult",
]

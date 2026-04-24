# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | rewrite to match real server contract | prev: 0.1.0
"""recall_client — official Python SDK for Recall memory server.

All Recall tools return ``{"result": str, "tool": str, "by": str}`` over HTTP.
This SDK exposes:

- ``RecallClient`` / ``AsyncRecallClient`` with one typed wrapper per registered tool.
- Generic ``call_tool(name, **kwargs) -> ToolResponse`` for anything new.

Quick start::

    from recall_client import RecallClient

    with RecallClient("http://localhost:8787", api_key="changeme") as c:
        c.remember("first memory", tags="hello,greeting")
        print(c.recall("hello", n=3).result)
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
from .models import ToolResponse

__version__ = "0.2.0"
__all__ = [
    "AsyncRecallClient",
    "RecallAuthError",
    "RecallClient",
    "RecallConnectionError",
    "RecallError",
    "RecallServerError",
    "RecallToolError",
    "ToolResponse",
]

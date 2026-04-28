# @wbx-modified copilot-b1c4 | 2026-04-27 19:30 MTN | v1.1 | structured envelope for recall + recall_filtered (port from server-azure v29.4) | prev: copilot-c4a1@2026-04-23
"""Plain HTTP transport — POST /tool/{name} with JSON body.

Used by browser-side UIs and any non-MCP client. Auth is enforced by the
ApiKeyAuthMiddleware applied at the app level.
"""

from __future__ import annotations

import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from ..store import is_ready
from ..tools import TOOL_REGISTRY
from ..tools.recall import _recall_structured
from ..tools.recall_filtered import _recall_filtered_structured

log = logging.getLogger("recall.transport.http")


# Tools that return a structured envelope {result, results} instead of a
# bare string. HTTP layer wraps with {tool, by} but does NOT cast result.
_STRUCTURED_TOOLS = {
    "recall": _recall_structured,
    "recall_filtered": _recall_filtered_structured,
}


async def health_handler(request: Request) -> JSONResponse:
    cfg = request.app.state.config
    if not is_ready():
        return JSONResponse({"status": "starting", "ready": False}, status_code=200)
    from ..store import get_store

    chunks = get_store().count()
    if cfg.min_expected_chunks > 0 and chunks < cfg.min_expected_chunks:
        return JSONResponse(
            {
                "status": "degraded",
                "chunks": chunks,
                "min_expected": cfg.min_expected_chunks,
                "ready": True,
            },
            status_code=503,
        )
    return JSONResponse(
        {"status": "ok", "chunks": chunks, "ready": True, "min_expected": cfg.min_expected_chunks}
    )


async def tool_handler(request: Request) -> JSONResponse:
    user = getattr(request.state, "user", "unknown")
    name = request.path_params.get("name", "")
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return JSONResponse(
            {"error": f"unknown tool: {name}", "available": sorted(TOOL_REGISTRY.keys())},
            status_code=404,
        )
    if not is_ready() and name != "memory_stats":
        return JSONResponse(
            {"error": "store still warming up, try again shortly"},
            status_code=503,
        )
    try:
        args = await request.json()
        if not isinstance(args, dict):
            return JSONResponse({"error": "body must be a JSON object"}, status_code=400)
    except Exception:
        args = {}
    log.info(
        "HTTP tool: %s by %s args=%s",
        name,
        user,
        {k: (v if isinstance(v, (int, float, bool)) else "<...>") for k, v in args.items()},
    )
    try:
        result = fn(**args)
    except TypeError as e:
        return JSONResponse({"error": f"bad arguments: {e}"}, status_code=400)
    except Exception as e:
        log.exception("Tool %s failed", name)
        return JSONResponse({"error": f"tool failed: {e}"}, status_code=500)
    structured = _STRUCTURED_TOOLS.get(name)
    if structured is not None:
        try:
            payload = structured(**args)
        except Exception:
            log.exception("Structured envelope for %s failed; falling back to string", name)
            payload = {"result": str(result), "results": []}
        return JSONResponse({**payload, "tool": name, "by": user})
    return JSONResponse({"result": str(result), "tool": name, "by": user})

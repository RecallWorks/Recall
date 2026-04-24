# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | plain HTTP transport | prev: NEW
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

log = logging.getLogger("recall.transport.http")


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
    return JSONResponse({"result": str(result), "tool": name, "by": user})

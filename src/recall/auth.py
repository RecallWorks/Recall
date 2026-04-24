# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | auth + hex session enforcement | prev: NEW
"""Authentication and session-id validation.

- ApiKeyAuthMiddleware: Starlette middleware enforcing X-API-Key on all
  routes except a small allow-list (/health, MCP transport).
- require_hex: write-side tools require a 4-hex agent id so every brain
  entry can be traced back to a specific agent session.
"""

from __future__ import annotations

import hmac
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_HEX_RE = re.compile(r"^(copilot-)?[0-9a-f]{4}$")


class BadSession(ValueError):
    """Raised when a session id fails the hex format check."""


def verify_key(api_keys: dict[str, str], candidate: str) -> str | None:
    """Return user name if `candidate` matches a valid key, else None.

    Uses hmac.compare_digest to defeat timing attacks.
    """
    for valid_key, name in api_keys.items():
        if hmac.compare_digest(candidate, valid_key):
            return name
    return None


def require_hex(value: str, param_name: str) -> str:
    """Return value if it matches the hex agent-id format, else raise BadSession."""
    if not value or not _HEX_RE.match(value):
        raise BadSession(
            f"ERROR: invalid {param_name}={value!r}. "
            "Mint a 4-char hex agent id (e.g. 'b4e7' or 'copilot-b4e7') and "
            f"pass it as the {param_name} parameter."
        )
    return value


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key on all routes except /health and MCP transport."""

    SKIP_AUTH = {"/health", "/sse", "/messages", "/messages/"}

    def __init__(self, app, api_keys: dict[str, str]) -> None:
        super().__init__(app)
        self._api_keys = api_keys

    async def dispatch(self, request, call_next):
        # Use request.url.path — the original path. scope["path"] gets
        # rewritten to "/" by Starlette Mount, breaking skip-auth matching.
        if request.url.path in self.SKIP_AUTH:
            return await call_next(request)
        key = request.headers.get("X-API-Key", "")
        # SSE EventSource in browsers can't set headers — accept query param too.
        if not key:
            key = request.query_params.get("api_key", "")
        user = verify_key(self._api_keys, key)
        if not user:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        request.state.user = user
        return await call_next(request)

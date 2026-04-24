# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — MCP/SSE transport adapter | prev: NEW
"""MCP/SSE transport — wraps the same TOOL_REGISTRY in a FastMCP server.

Lazy import so plain-HTTP deployments don't require the mcp package.
"""
from __future__ import annotations


def build_mcp_server(name: str = "recall"):
    """Return a FastMCP server with all tools registered."""
    from mcp.server import FastMCP
    from mcp.server.transport_security import TransportSecuritySettings

    from ..tools import TOOL_REGISTRY

    mcp = FastMCP(
        name,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    for tool_name, fn in TOOL_REGISTRY.items():
        # Re-decorate each function so FastMCP picks it up. The decorator
        # uses the function's __name__, so we wrap to match tool_name.
        fn.__name__ = tool_name  # ensure registration name matches
        mcp.tool()(fn)
    return mcp

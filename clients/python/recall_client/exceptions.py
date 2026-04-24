# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | typed exceptions | prev: NEW
"""Exceptions raised by the Recall SDK."""

from __future__ import annotations


class RecallError(Exception):
    """Base exception for all Recall SDK errors."""


class RecallConnectionError(RecallError):
    """Raised when the server cannot be reached."""


class RecallAuthError(RecallError):
    """Raised when the API key is missing or invalid (HTTP 401/403)."""


class RecallServerError(RecallError):
    """Raised when the server returns 5xx."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class RecallToolError(RecallError):
    """Raised when a tool call returns an explicit error payload."""

    def __init__(self, tool: str, message: str):
        super().__init__(f"{tool}: {message}")
        self.tool = tool

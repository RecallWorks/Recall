# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | unit tests for real-contract SDK | prev: typed-Hit fiction
"""Unit tests for the sync and async Recall clients (0.2.0 contract)."""

from __future__ import annotations

import httpx
import pytest
import respx

from recall_client import (
    AsyncRecallClient,
    RecallAuthError,
    RecallClient,
    RecallConnectionError,
    RecallServerError,
    RecallToolError,
)

BASE_URL = "http://localhost:8787"
API_KEY = "test-key"


def _envelope(result: str, tool: str, by: str = "test-user") -> dict:
    return {"result": result, "tool": tool, "by": by}


@pytest.fixture
def client():
    with RecallClient(BASE_URL, api_key=API_KEY) as c:
        yield c


@respx.mock
def test_remember_returns_tool_response(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(200, json=_envelope("Stored 1 chunk", "remember"))
    )
    r = client.remember("hello", tags="greeting,ui")
    assert r.tool == "remember"
    assert "Stored" in r.result


@respx.mock
def test_remember_sends_string_tags(client):
    route = respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(200, json=_envelope("ok", "remember"))
    )
    client.remember("x", tags="a,b")
    body = route.calls.last.request.content.decode()
    assert '"tags":"a,b"' in body
    assert '"source":"agent-observation"' in body


@respx.mock
def test_recall_uses_n_param(client):
    route = respx.post(f"{BASE_URL}/tool/recall").mock(
        return_value=httpx.Response(200, json=_envelope("# Hits\n- foo", "recall"))
    )
    client.recall("query", n=3)
    body = route.calls.last.request.content.decode()
    assert '"n":3' in body
    assert '"type":"all"' in body


@respx.mock
def test_forget_takes_source_not_id(client):
    route = respx.post(f"{BASE_URL}/tool/forget").mock(
        return_value=httpx.Response(200, json=_envelope("Archived 5", "forget"))
    )
    client.forget("agent-observation")
    body = route.calls.last.request.content.decode()
    assert '"source":"agent-observation"' in body


@respx.mock
def test_checkpoint_real_signature(client):
    route = respx.post(f"{BASE_URL}/tool/checkpoint").mock(
        return_value=httpx.Response(
            200, json=_envelope("Checkpoint stored", "checkpoint")
        )
    )
    client.checkpoint(
        intent="ship SDK",
        established="contract verified",
        pursuing="live smoke",
        open_questions="none",
        session="a3f7",
    )
    body = route.calls.last.request.content.decode()
    assert '"intent":"ship SDK"' in body
    assert '"session":"a3f7"' in body


@respx.mock
def test_auth_error_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    with pytest.raises(RecallAuthError):
        client.remember("x")


@respx.mock
def test_server_error_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(500, text="boom")
    )
    with pytest.raises(RecallServerError) as exc:
        client.remember("x")
    assert exc.value.status_code == 500


@respx.mock
def test_tool_error_payload_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(400, json={"error": "bad arguments: missing content"})
    )
    with pytest.raises(RecallToolError):
        client.remember("x")


@respx.mock
def test_connection_error_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(side_effect=httpx.ConnectError("nope"))
    with pytest.raises(RecallConnectionError):
        client.remember("x")


@respx.mock
def test_call_tool_generic_dispatch(client):
    respx.post(f"{BASE_URL}/tool/maintenance").mock(
        return_value=httpx.Response(
            200, json=_envelope("Maintenance complete", "maintenance")
        )
    )
    r = client.call_tool("maintenance", pull=True)
    assert r.tool == "maintenance"


@respx.mock
def test_health_no_auth_path(client):
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "ready": True, "chunks": 0}
        )
    )
    h = client.health()
    assert h["status"] == "ok"


@respx.mock
def test_x_api_key_header_sent(client):
    route = respx.post(f"{BASE_URL}/tool/pulse").mock(
        return_value=httpx.Response(200, json=_envelope("# Pulse", "pulse"))
    )
    client.pulse()
    assert route.calls.last.request.headers["X-API-Key"] == API_KEY


@respx.mock
def test_unknown_tool_404_is_tool_error(client):
    respx.post(f"{BASE_URL}/tool/bogus").mock(
        return_value=httpx.Response(404, json={"error": "unknown tool: bogus"})
    )
    with pytest.raises(RecallToolError):
        client.call_tool("bogus")


# ── async ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_async_remember():
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(200, json=_envelope("ok", "remember"))
    )
    async with AsyncRecallClient(BASE_URL, api_key=API_KEY) as c:
        r = await c.remember("hi")
        assert r.tool == "remember"


@pytest.mark.asyncio
@respx.mock
async def test_async_recall_envelope():
    respx.post(f"{BASE_URL}/tool/recall").mock(
        return_value=httpx.Response(200, json=_envelope("# Hits", "recall"))
    )
    async with AsyncRecallClient(BASE_URL, api_key=API_KEY) as c:
        r = await c.recall("q", n=2)
        assert r.tool == "recall"


@pytest.mark.asyncio
@respx.mock
async def test_async_auth_error():
    respx.post(f"{BASE_URL}/tool/recall").mock(return_value=httpx.Response(403))
    async with AsyncRecallClient(BASE_URL, api_key="bad") as c:
        with pytest.raises(RecallAuthError):
            await c.recall("q")

# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | Python SDK tests w/ respx | prev: NEW
"""Unit tests for the sync and async Recall clients.

Uses respx to stub httpx calls — no real server needed.
"""

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


@pytest.fixture
def client():
    with RecallClient(BASE_URL, api_key=API_KEY) as c:
        yield c


@respx.mock
def test_remember_returns_id(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(200, json={"id": "abc123", "artifact_path": "/d/abc.md"})
    )
    result = client.remember("hello world", tags=["greeting"])
    assert result.id == "abc123"
    assert result.artifact_path == "/d/abc.md"


@respx.mock
def test_recall_returns_typed_hits(client):
    respx.post(f"{BASE_URL}/tool/recall").mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": [
                    {"id": "1", "content": "first hit", "score": 0.95, "tags": ["a"]},
                    {"id": "2", "content": "second hit", "score": 0.81, "tags": []},
                ]
            },
        )
    )
    hits = client.recall("query", limit=2)
    assert len(hits) == 2
    assert hits[0].content == "first hit"
    assert hits[0].score == 0.95
    assert hits[0].tags == ["a"]


@respx.mock
def test_recall_handles_results_key_alias(client):
    """Some Recall tool variants return 'results' instead of 'hits'."""
    respx.post(f"{BASE_URL}/tool/recall").mock(
        return_value=httpx.Response(
            200, json={"results": [{"content": "x", "score": 0.5}]}
        )
    )
    hits = client.recall("q")
    assert len(hits) == 1
    assert hits[0].content == "x"


@respx.mock
def test_auth_error_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(401, text="bad key")
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
        return_value=httpx.Response(200, json={"error": "invalid tag format"})
    )
    with pytest.raises(RecallToolError) as exc:
        client.remember("x")
    assert "invalid tag format" in str(exc.value)


@respx.mock
def test_connection_error_raises(client):
    respx.post(f"{BASE_URL}/tool/remember").mock(side_effect=httpx.ConnectError("nope"))
    with pytest.raises(RecallConnectionError):
        client.remember("x")


@respx.mock
def test_call_tool_generic_dispatch(client):
    respx.post(f"{BASE_URL}/tool/index_file").mock(
        return_value=httpx.Response(200, json={"chunks": 7})
    )
    result = client.call_tool("index_file", path="/data/notes.md")
    assert result == {"chunks": 7}


@respx.mock
def test_health(client):
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "uptime": 1234})
    )
    h = client.health()
    assert h["status"] == "ok"


@respx.mock
def test_authorization_header_sent(client):
    route = respx.post(f"{BASE_URL}/tool/pulse").mock(
        return_value=httpx.Response(200, json={"sessions": 0})
    )
    client.pulse()
    assert route.calls.last.request.headers["Authorization"] == f"Bearer {API_KEY}"


# ── async client tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_async_remember():
    respx.post(f"{BASE_URL}/tool/remember").mock(
        return_value=httpx.Response(200, json={"id": "async-1"})
    )
    async with AsyncRecallClient(BASE_URL, api_key=API_KEY) as c:
        result = await c.remember("hi")
        assert result.id == "async-1"


@pytest.mark.asyncio
@respx.mock
async def test_async_recall():
    respx.post(f"{BASE_URL}/tool/recall").mock(
        return_value=httpx.Response(
            200, json={"hits": [{"content": "h", "score": 0.9}]}
        )
    )
    async with AsyncRecallClient(BASE_URL, api_key=API_KEY) as c:
        hits = await c.recall("q")
        assert len(hits) == 1


@pytest.mark.asyncio
@respx.mock
async def test_async_auth_error():
    respx.post(f"{BASE_URL}/tool/recall").mock(return_value=httpx.Response(403))
    async with AsyncRecallClient(BASE_URL, api_key="bad") as c:
        with pytest.raises(RecallAuthError):
            await c.recall("q")

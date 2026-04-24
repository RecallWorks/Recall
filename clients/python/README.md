<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | Python SDK README | prev: NEW -->
# recall-client (Python)

Official Python SDK for [Recall](https://github.com/RecallWorks/Recall) — open-source memory for AI agents.

## Install

```bash
pip install recall-client
```

## Quick start

```python
from recall_client import RecallClient

with RecallClient("http://localhost:8787", api_key="changeme") as client:
    print(client.health())  # {"status": "ok", "chunks": ..., "ready": True}

    client.remember("the user prefers dark mode", tags="pref,ui")
    res = client.recall("user preferences", n=5)
    print(res.result)  # markdown listing of hits
```

Every tool returns a `ToolResponse` envelope with three string fields: `result`, `tool`, `by`. The server formats results as markdown — parse `result` if you need structured fields.

## Async

```python
import asyncio
from recall_client import AsyncRecallClient

async def main():
    async with AsyncRecallClient("http://localhost:8787", api_key="changeme") as c:
        await c.remember("async memory works", tags="async")
        res = await c.recall("memory")
        print(res.result)

asyncio.run(main())
```

## Tool surface

The client exposes typed wrappers for the high-traffic tools:

| Method | Recall tool |
|--------|-------------|
| `remember()` | `remember` |
| `recall()` | `recall` |
| `reflect()` | `reflect` |
| `checkpoint()` | `checkpoint` |
| `pulse()` | `pulse` |
| `memory_stats()` | `memory_stats` |
| `forget()` | `forget` |
| `health()` | `GET /health` |

All 13 server tools have typed wrappers (`remember`, `recall`, `reflect`, `anti_pattern`, `session_close`, `checkpoint`, `pulse`, `memory_stats`, `forget`, `reindex`, `index_file`, `maintenance`, `snapshot_index`). For any custom or future tool, use the generic dispatch:

```python
client.call_tool("index_file", filepath="/data/notes.md")
client.call_tool("forget", source="agent-observation")
```

> Note: `forget()` takes a `source` label and **soft-archives** every chunk with that source. It does not delete a single chunk by id.

## Errors

All exceptions derive from `RecallError`:

- `RecallConnectionError` — server unreachable
- `RecallAuthError` — 401/403 (bad/missing API key)
- `RecallServerError` — 5xx
- `RecallToolError` — tool returned an explicit `error`

## License

MIT. See [LICENSE](https://github.com/RecallWorks/Recall/blob/main/LICENSE) at the root of the Recall repo.

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
    client.remember("the user prefers dark mode", tags=["pref", "ui"])
    hits = client.recall("user preferences", limit=5)
    for h in hits:
        print(f"{h.score:.3f}  {h.content}")
```

## Async

```python
import asyncio
from recall_client import AsyncRecallClient

async def main():
    async with AsyncRecallClient("http://localhost:8787", api_key="changeme") as c:
        await c.remember("async memory works", tags=["async"])
        hits = await c.recall("memory")
        print(hits)

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

For any tool without a typed wrapper (e.g. `index_file`, `reindex`, `snapshot_index`, `anti_pattern`, `session_close`, `maintenance`), use the generic dispatch:

```python
client.call_tool("index_file", path="/data/notes.md")
client.call_tool("anti_pattern", pattern="don't auto-merge without CI")
```

## Errors

All exceptions derive from `RecallError`:

- `RecallConnectionError` — server unreachable
- `RecallAuthError` — 401/403 (bad/missing API key)
- `RecallServerError` — 5xx
- `RecallToolError` — tool returned an explicit `error`

## License

MIT. See [LICENSE](https://github.com/RecallWorks/Recall/blob/main/LICENSE) at the root of the Recall repo.

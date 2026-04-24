<!-- @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 5 — quickstart | prev: NEW -->
# Quickstart

Get a single-tenant Recall server running and storing memories in under five
minutes.

## 1. Run the container

```bash
docker run -d --name recall \
  -p 8787:8787 \
  -e API_KEY=changeme \
  -v recall-data:/data \
  ghcr.io/recallworks/recall:latest
```

> Building from source instead? See [docker/README.md](../docker/README.md).

## 2. Verify

```bash
curl http://localhost:8787/health
# {"status":"ok","chunks":0,"ready":true,"min_expected":0}
```

## 3. Store a memory

```bash
curl -X POST http://localhost:8787/tool/remember \
  -H "X-API-Key: changeme" \
  -H "Content-Type: application/json" \
  -d '{"content":"Postgres connection pool maxes at 20 by default","source":"team-discovery","tags":"db,perf"}'
```

## 4. Recall it

```bash
curl -X POST http://localhost:8787/tool/recall \
  -H "X-API-Key: changeme" \
  -H "Content-Type: application/json" \
  -d '{"query":"connection pool size","n":3}'
```

## 5. Wire it into your agent

Pick a transport:

- **MCP / SSE** — for clients that speak the Model Context Protocol (Copilot
  Chat with MCP, Claude Desktop, Cursor, etc). Endpoint: `/sse`.
- **Plain HTTP** — for any other agent. POST to `/tool/{name}` with a JSON body.

See [conventions/cold-start-ritual.md](conventions/cold-start-ritual.md) for the
opening protocol every session should run.

## What you just got

Thirteen tools backed by ChromaDB:

| Tool             | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `recall`         | Semantic search across all memory                              |
| `remember`       | Store a free-form observation                                  |
| `reflect`        | Store a structured reasoning artifact (hypothesis → result)    |
| `anti_pattern`   | Store a "looks-right-but-isn't" warning                        |
| `checkpoint`     | Snapshot working state (intent / established / pursuing / open)|
| `pulse`          | Read back the latest checkpoint + reasoning + anti-patterns    |
| `session_close`  | End-of-session reflection                                      |
| `reindex`        | Re-scan files into the store                                   |
| `index_file`     | Index one file                                                 |
| `memory_stats`   | Counts and source list                                         |
| `forget`         | **Archive** (not delete) all chunks from a source              |
| `snapshot_index` | Persist the live store to durable storage                      |
| `maintenance`    | git pull → reindex → warm query → snapshot                     |

## Next

- [Conventions](conventions/) — the routing.md / pulse / branding patterns
- [Docker guide](../docker/README.md) — production-ish single-tenant setup
- [Architecture](architecture.md) — what's inside

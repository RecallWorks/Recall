<!-- @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 5 — architecture overview | prev: NEW -->
# Architecture

## Components

```text
┌─────────────────────────────────────────────────┐
│  Transport                                      │
│   ├─ HTTP (POST /tool/{name})                   │
│   ├─ MCP / SSE  (mounted FastMCP)               │
│   └─ /health  (no auth)                         │
└──────────────────┬──────────────────────────────┘
                   │  ApiKeyAuthMiddleware
                   ▼
┌─────────────────────────────────────────────────┐
│  Tools (TOOL_REGISTRY)                          │
│   recall · remember · reflect · anti_pattern    │
│   checkpoint · pulse · session_close            │
│   reindex · index_file · forget · stats         │
│   maintenance · snapshot_index                  │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐      ┌──────────────────┐
│  Store       │      │  Artifacts       │
│  (Chroma)    │      │  (.md on disk)   │
│  ephemeral   │      │  durable         │
└──────┬───────┘      └──────────────────┘
       │  snapshot_index()
       ▼
┌──────────────┐
│  PREBUILT    │  ← boot hydration source
│  durable     │
└──────────────┘
```

## Data lifecycle

1. **Write tool** is called (`remember`, `reflect`, `checkpoint`, …).
2. Chunk is upserted into the live ChromaDB store on local disk.
3. The same content is appended as a `.md` file under `ARTIFACTS_DIR` —
   this is the source of truth that survives container loss.
4. Every Nth write (`AUTO_SNAPSHOT_EVERY`) triggers `snapshot_index()`
   which atomically copies the live store into `PREBUILT_DIR` on durable
   storage.
5. On container restart, the entrypoint hydrates the live store from
   `PREBUILT_DIR` so the new container boots whole.

## Why this layout

- **Live store on local disk** — ChromaDB uses SQLite. SQLite file locks
  deadlock on SMB/NFS network shares. The live store has to be local.
- **Snapshot to durable storage** — Without snapshots, every container
  restart loses all writes since the last image build. Snapshots make the
  store as durable as the underlying volume.
- **Append-only artifacts** — Even if both the live store and the snapshot
  are lost, you can rebuild the entire history by reindexing the artifacts
  directory.

## What's pluggable

- **Store backend** — `recall.store.Store` is a Protocol. Drop in Qdrant /
  Pinecone / pgvector / in-memory by implementing five methods.
- **Transport** — HTTP and MCP/SSE share the same `TOOL_REGISTRY`. Add a
  WebSocket or gRPC adapter without touching tool code.
- **Auth** — `ApiKeyAuthMiddleware` is one Starlette middleware. Swap for
  OAuth/SAML/JWT by replacing it.

## What's intentionally NOT pluggable in v0.1

- Embedding model (uses ChromaDB's bundled default).
- Chunking strategy (fixed-size with overlap).
- Sharding / multi-tenant routing (lives in the `enterprise/` tier).

<!-- @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 3 — Docker quickstart | prev: NEW -->
# Recall — Single-Tenant Docker

The fastest way to run Recall on your own machine or a single VM.

## Build

```bash
cd recall   # repo root
docker build -t recall:latest -f docker/single-tenant/Dockerfile .
```

## Run

```bash
docker run -d --name recall \
  -p 8787:8787 \
  -e API_KEY=your-secret \
  -v recall-data:/data \
  recall:latest
```

Verify:

```bash
curl http://localhost:8787/health
# {"status":"ok","chunks":0,"ready":true,"min_expected":0}

curl -X POST http://localhost:8787/tool/memory_stats \
  -H "X-API-Key: your-secret" \
  -H "Content-Type: application/json" -d '{}'
```

## Or with compose

```bash
RECALL_API_KEY=your-secret docker compose -f docker/single-tenant/docker-compose.yml up -d
```

## Volume layout

The container writes durable state under `/data`:

```text
/data/
├── prebuilt-index/   # snapshot of the live ChromaDB store (boot-hydration source)
├── artifacts/        # remember/reflect/anti_pattern/checkpoint .md files
└── repo/             # cloned knowledge repo (if GIT_REPO_URL is set)
```

The live ChromaDB store lives at `/app/chromadb-store` (ephemeral on purpose —
SQLite locks deadlock on network filesystems). It's hydrated from
`/data/prebuilt-index` on every container start, and `snapshot_index()` /
`AUTO_SNAPSHOT_EVERY` keep that snapshot fresh.

## Environment variables

| Var                   | Default                    | Notes                                    |
|-----------------------|----------------------------|------------------------------------------|
| `API_KEY`             | (required)                 | Single-user key                          |
| `API_KEYS`            | (alternative)              | JSON map `{"alice":"key1",...}`          |
| `STORE_DIR`           | `/app/chromadb-store`      | Live store. Keep on local disk.          |
| `PREBUILT_DIR`        | `/data/prebuilt-index`     | Durable snapshot target.                 |
| `ARTIFACTS_DIR`       | `/data/artifacts`          | Append-only `.md` artifact log.          |
| `REPO_DIR`            | `/data/repo`               | Clone destination for `GIT_REPO_URL`.    |
| `GIT_REPO_URL`        | (unset)                    | Optional knowledge repo to index on boot.|
| `INDEX_DIRS`          | `knowledge,docs`           | Subdirs of `REPO_DIR` to index.          |
| `FILE_EXTENSIONS`     | `.md,.txt`                 | What to index.                           |
| `AUTO_SNAPSHOT_EVERY` | `50`                       | Auto-snapshot after N writes.            |
| `MIN_EXPECTED_CHUNKS` | `0`                        | If >0, `/health` 503s when below floor.  |
| `HOST`                | `0.0.0.0`                  | Bind addr.                               |
| `PORT`                | `8787`                     |                                          |

## Troubleshooting

- **`/health` returns `{"status":"starting"}` for a long time** — first boot indexes
  the repo + warms the embedding model. ~30-60s on a small box, longer if cloning.
- **Writes "succeed" but disappear after `docker restart`** — your `PREBUILT_DIR`
  isn't on the mounted volume. Confirm `docker inspect recall | grep -A2 Mounts`.
- **`ConnectionRefusedError`** on the host — check the bind: container is on
  `0.0.0.0:8787` but `docker ps` will show what host port that maps to.

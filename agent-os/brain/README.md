# Recall · Networked Brain

A small HTTP+SSE service wrapping ChromaDB. Multiple agents (multiple
machines, multiple users) can share recall, remember, reflect, checkpoint
primitives over the wire.

This is **v0.2 territory** — the current published files are a blueprint, not
a one-click build. The pattern below is verified in production at the
originating workstation (call it `<your-brain-host>`); the public packaging
is being de-personalized.

## What's in this folder

- `Dockerfile` — base image: `python:3.12-slim`, installs `chromadb`,
  `fastapi`, `uvicorn`, `sentence-transformers`. ~1.2 GB final.
- `docker-compose.yml` — one-service compose with a named volume for the
  vector store, port 8080 exposed.
- `recall.py` — HTTP+SSE service. Implements 16 tools (recall, remember,
  reflect, checkpoint, anti_pattern, forget, index_file, reindex,
  memory_stats, pulse, session_close, etc.).
- `agency_sidecar_patch.md` — design note explaining why a frozen
  prebuilt-index ChromaDB collection plus a writable sidecar collection
  in the SAME persistent client is the right pattern when you want to
  ship sealed reference content alongside per-tenant scratch space.

## The pattern that matters

The reference architecture is **frozen-read + sidecar-write + merge on query.**

- One ChromaDB collection ships with the image, sealed (HNSW segment
  read-only). It contains your foundation corpus — RFCs, agency docs,
  internal references. It never changes.
- A second ChromaDB collection is created lazily in the same persistent
  client. It accepts writes. It holds session memory, anti-patterns,
  user-specific reflections.
- `recall()` queries both, merges by distance, returns the top-N.
- Backup → only the writable sidecar needs snapshotting (the frozen
  collection regenerates from image rebuild).

That's it. The HTTP shell on top of it is mechanical.

## What's NOT here yet

- Full `recall.py` source, de-personalized. Coming with the v0.2 image.
- `agency_loader.py` — script for loading new corpus into the writable
  sidecar via stable IDs (`sha256(collection:path)[:16]`).
- Multi-tenant auth (currently the originating implementation uses a
  single shared `X-API-Key` header per machine; SaaS-grade auth is
  deliberately deferred).
- Coordination primitives (`claim` / `release` / `who_has` / `handoff`).
  Designed but not yet open-sourced; v0.3.

## Why this is in v0.2 not v0.1

The whitepaper (`site/agent-os.html`) describes the architecture. The
pattern is the deliverable. A working reference image is a quality-of-life
add-on. Ship the spec, then the impl. This avoids the trap where the public
release is a one-machine-only artifact.

If you want to build it yourself today, this is enough:

```bash
pip install chromadb fastapi uvicorn[standard] sentence-transformers
# Implement the 16 tools listed above as FastAPI endpoints, each
# delegating to one of two ChromaDB collections (frozen + sidecar)
# in a single PersistentClient.
# Wire SSE for the streaming endpoints (recall, reflect).
# Mount /data as a docker volume.
```

The originating implementation runs at ~50 chunks/sec on a single 5080-class
GPU embedder, ~5 MB RAM idle, ~1.5 GB with the foundation corpus loaded.

## Reference

The originating brain is part of an internal project named "IceWhisperer" in
the originating workstation. The architecture note that documents the
frozen-read + writable-sidecar trick lives in
`reference/icewhisperer/icewhisperer-brain-architecture.md` of that project's
memory dir. It will be re-published here as `agency_sidecar_patch.md` once
de-personalized.

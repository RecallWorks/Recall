#!/bin/sh
# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 3 — boot hydration from durable snapshot | prev: NEW
set -e

STORE_DIR="${STORE_DIR:-/app/chromadb-store}"
PREBUILT_DIR="${PREBUILT_DIR:-/data/prebuilt-index}"

# If a durable snapshot exists and the live store is empty, hydrate.
# This is what survives container restarts.
if [ -d "$PREBUILT_DIR" ] && [ -z "$(ls -A "$STORE_DIR" 2>/dev/null)" ]; then
  echo "[entrypoint] Hydrating $STORE_DIR from $PREBUILT_DIR ..."
  cp -a "$PREBUILT_DIR"/. "$STORE_DIR"/ || echo "[entrypoint] hydration copy failed (continuing)"
fi

exec "$@"

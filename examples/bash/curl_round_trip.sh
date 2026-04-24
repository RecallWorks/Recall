#!/usr/bin/env bash
# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | raw HTTP round trip — no SDK
#
# Run a server first:
#   docker run -d -p 8787:8787 -e API_KEY=changeme \
#     -v recall-data:/data ghcr.io/recallworks/recall:latest

set -euo pipefail

URL="${RECALL_URL:-http://localhost:8787}"
KEY="${RECALL_KEY:-changeme}"

echo "== health =="
curl -s "$URL/health"
echo

echo "== remember =="
curl -s -X POST "$URL/tool/remember" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"content":"the project deadline is 2026-05-15","source":"project","tags":"deadline"}'
echo

echo "== recall =="
curl -s -X POST "$URL/tool/recall" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"when is the deadline","n":3}'
echo

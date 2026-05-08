# @wbx-modified copilot-a3f7·MTN | 2026-05-08 | v0.5.1 | top-level Dockerfile pointer for crawlers (Glama/awesome-mcp listings); canonical build is docker/single-tenant/Dockerfile | prev: (none)
# syntax=docker/dockerfile:1.6
#
# Recall - open-source MCP memory server for AI coding agents.
#   Repo:      https://github.com/RecallWorks/Recall
#   Site:      https://www.recall.works
#   PyPI:      pip install ai-recallworks
#
# This is a thin top-level Dockerfile so listing crawlers (Glama, awesome-mcp,
# etc.) and "docker build ." work out of the box. The full multi-stage build
# (with entrypoint, health check, volume layout) lives at
# docker/single-tenant/Dockerfile - it is build-equivalent to this one.
#
# Build:  docker build -t recall:latest .
# Run:    docker run -p 8787:8787 -e API_KEY=secret -v recall-data:/data recall:latest
# Health: curl http://localhost:8787/health

FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 --shell /bin/bash recall

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade "pip==24.2" \
 && pip install --no-cache-dir --retries 5 --timeout 60 ".[llm,mcp]"

ENV STORE_DIR=/app/chromadb-store \
    PREBUILT_DIR=/data/prebuilt-index \
    ARTIFACTS_DIR=/data/artifacts \
    REPO_DIR=/data/repo \
    HOST=0.0.0.0 \
    PORT=8787 \
    PYTHONUNBUFFERED=1

RUN mkdir -p "$STORE_DIR" "$PREBUILT_DIR" "$ARTIFACTS_DIR" "$REPO_DIR" \
 && chown -R recall:recall /app /data 2>/dev/null || true

VOLUME ["/data"]
EXPOSE 8787
USER recall

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8787/health',timeout=3); sys.exit(0 if r.status==200 else 1)" || exit 1

CMD ["recall-server"]

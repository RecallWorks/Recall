# @wbx-modified copilot-b1c4 | 2026-04-27 23:36 MTN | v0.3.3 | install [llm,mcp] so SSE + recall-mcp work | prev: copilot-a3f7@2026-04-26
# syntax=docker/dockerfile:1.6
#
# Recall — single-tenant agent-memory MCP server.
# Build:   docker build -t recall:latest -f docker/single-tenant/Dockerfile .
# Run:     docker run -p 8787:8787 -e API_KEY=secret -v recall-data:/data recall:latest
# Health:  curl http://localhost:8787/health

# Pinned to 3.12-slim: widest wheel coverage (chromadb, onnxruntime, etc.).
# pyproject requires-python >=3.11, so 3.12 is in-band. Avoid 3.14 until upstream
# wheel matrix catches up (was the cause of intermittent GHA build failures).
FROM python:3.12-slim AS base

# Install git for optional GIT_REPO_URL sync. Stay minimal otherwise.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --create-home --uid 10001 --shell /bin/bash recall

WORKDIR /app

# ---- Dependency layer (cached when src/ changes but pyproject doesn't) ----
# Pin pip and use --retries to ride through transient PyPI/index hiccups.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade "pip==24.2" \
 && pip install --no-cache-dir --retries 5 --timeout 60 ".[llm,mcp]"

# ---- Runtime layout ----
# Ephemeral local store (ChromaDB SQLite — must NOT be on a network share).
# Durable artifacts + prebuilt snapshot live under /data (mount a volume here).
ENV STORE_DIR=/app/chromadb-store \
    PREBUILT_DIR=/data/prebuilt-index \
    ARTIFACTS_DIR=/data/artifacts \
    REPO_DIR=/data/repo \
    HOST=0.0.0.0 \
    PORT=8787 \
    AUTO_SNAPSHOT_EVERY=50 \
    PYTHONUNBUFFERED=1

RUN mkdir -p "$STORE_DIR" "$PREBUILT_DIR" "$ARTIFACTS_DIR" "$REPO_DIR" \
 && chown -R recall:recall /app /data 2>/dev/null || true

VOLUME ["/data"]
EXPOSE 8787

USER recall

# Boot script: hydrate STORE_DIR from PREBUILT_DIR if present, then start server.
COPY --chown=recall:recall docker/single-tenant/entrypoint.sh /usr/local/bin/recall-entrypoint
# (chmod is honored by Docker on copy if `--chmod=` is set; but we use a shebang
# and exec via `sh` for portability.)

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8787/health',timeout=3); sys.exit(0 if r.status==200 else 1)" || exit 1

ENTRYPOINT ["sh", "/usr/local/bin/recall-entrypoint"]
CMD ["recall-server"]

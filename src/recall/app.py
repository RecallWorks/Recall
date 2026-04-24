# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | app entry — composes config + store + transports | prev: NEW
"""Application entry point.

Builds a Starlette app with:
  - ApiKeyAuthMiddleware
  - GET /health
  - POST /tool/{name}
  - MCP/SSE routes (mounted from FastMCP)

Background thread initializes ChromaDB + optional git sync + initial index.
"""
from __future__ import annotations

import logging
import os
import threading

from starlette.applications import Starlette
from starlette.routing import Route

from .auth import ApiKeyAuthMiddleware
from .config import Config
from .embedder import make_embedder_from_env
from .git_sync import git_sync, resolve_index_paths
from .store import init_store
from .summarizer import init_summarizer, make_summarizer_from_env
from .tools import TOOL_REGISTRY  # noqa: F401  (ensure registry assembled at import)
from .tools import recall as _recall_mod
from .tools import remember as _remember_mod
from .tools import reindex as _reindex_mod
from .tools import stats as _stats_mod
from .tools import reflect as _reflect_mod
from .tools import checkpoint as _checkpoint_mod
from .tools import maintenance as _maintenance_mod
from .transport.http import health_handler, tool_handler

log = logging.getLogger("recall.app")


def _propagate_config(cfg: Config) -> None:
    """Push the active Config into every tool module's lazy default."""
    for mod in (_recall_mod, _remember_mod, _reindex_mod, _stats_mod,
                _reflect_mod, _checkpoint_mod, _maintenance_mod):
        mod.set_config(cfg)


def _background_init(cfg: Config) -> None:
    """Heavy startup tasks — runs in a daemon thread so the HTTP port binds fast."""
    log.info("Background init: initializing store at %s", cfg.store_dir)

    # BYO embedder + summarizer. Both fall back to fully-offline defaults if
    # no env vars are set, so a fresh `docker run` works out of the box.
    try:
        embedder = make_embedder_from_env()
    except Exception:
        log.exception("Embedder init failed; using bundled default")
        from .embedder import DefaultChromaEmbedder
        embedder = DefaultChromaEmbedder()

    try:
        init_summarizer(make_summarizer_from_env())
    except Exception:
        log.exception("Summarizer init failed; using noop")
        from .summarizer import NoopSummarizer, init_summarizer as _is
        _is(NoopSummarizer())

    try:
        init_store(cfg.store_dir, cfg.collection_name, embedder=embedder)
    except Exception:
        log.exception("Store init failed")
        return

    if cfg.git_repo_url:
        try:
            git_sync(cfg.git_repo_url, cfg.repo_dir, cfg.git_token)
        except Exception:
            log.exception("git_sync failed (non-fatal)")

    paths = resolve_index_paths(cfg.repo_dir, cfg.index_dirs, cfg.artifacts_dir)
    from .store import get_store
    if get_store().count() == 0 and paths:
        log.info("Empty store — running initial maintenance")
        try:
            result = _maintenance_mod.maintenance(pull=False)
            log.info("Initial maintenance: %s", result)
        except Exception:
            log.exception("Initial maintenance failed (non-fatal)")
    log.info("Background init complete. Chunks: %d", get_store().count())


def build_app(cfg: Config | None = None, *, start_background: bool = True) -> Starlette:
    """Construct the Starlette app. Pass start_background=False in tests."""
    cfg = cfg or Config.from_env()
    _propagate_config(cfg)

    routes = [
        Route("/health", health_handler, methods=["GET"]),
        Route("/tool/{name}", tool_handler, methods=["POST"]),
    ]
    app = Starlette(routes=routes)
    app.state.config = cfg
    app.add_middleware(ApiKeyAuthMiddleware, api_keys=cfg.api_keys)

    if start_background:
        for d in (cfg.store_dir, cfg.artifacts_dir, cfg.repo_dir):
            os.makedirs(d, exist_ok=True)
        threading.Thread(target=_background_init, args=(cfg,), daemon=True).start()
    return app


def main() -> None:
    """uvicorn entry. `python -m recall` or `recall-server` console script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    import uvicorn

    cfg = Config.from_env()
    app = build_app(cfg)
    log.info("Starting Recall on %s:%d", cfg.host, cfg.port)
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="info")


if __name__ == "__main__":
    main()

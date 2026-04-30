# @wbx-modified copilot-a3f7 | 2026-04-29 23:59 MTN | v1.1 | zero-config stdio: synthesize local API key if not set (VS Code MCP gallery / Claude Desktop one-shot install) | prev: copilot-b1c4@2026-04-27 22:20 MTN
"""Stdio MCP server entry point.

This is what Claude Desktop, Cursor, Cline, Continue.dev, and other MCP
clients consume via subprocess + JSON-RPC over stdin/stdout. Run via:

    python -m recall.mcp_stdio

or via the console script:

    recall-mcp

It composes the same Config, embedder, summarizer, and store as the HTTP
server, then hands stdio to FastMCP.

Environment variables (all optional — sensible defaults for local use):
  API_KEY              auth key for tool calls    (default: 'stdio-local' synthesized)
  STORE_DIR            chroma + sqlite location   (default: ~/.recall/store)
  ARTIFACTS_DIR        markdown notes location    (default: ~/.recall/artifacts)
  COLLECTION_NAME      chroma collection name     (default: recall_memory)
  RECALL_EMBEDDER      'default' (offline) | 'openai' | 'ollama' | 'voyage'
  OPENAI_API_KEY       required if RECALL_EMBEDDER=openai
  VOYAGE_API_KEY       required if RECALL_EMBEDDER=voyage

Note: stdio MCP servers MUST NOT print to stdout — that channel is the
MCP transport. All logs go to stderr.
"""

from __future__ import annotations

import logging
import os
import sys


def main() -> None:
    """Initialize stores, then run FastMCP over stdio."""
    # Logs to stderr ONLY (stdout is the MCP transport)
    logging.basicConfig(
        level=os.environ.get("RECALL_LOG_LEVEL", "WARNING").upper(),
        format="%(asctime)s [%(levelname)s recall.mcp] %(message)s",
        stream=sys.stderr,
    )
    log = logging.getLogger("recall.mcp_stdio")

    from .config import Config
    from .embedder import make_embedder_from_env
    from .store import init_store
    from .summarizer import init_summarizer, make_summarizer_from_env
    from .tools import (
        checkpoint as _checkpoint_mod,
    )
    from .tools import (
        coordinate as _coordinate_mod,
    )
    from .tools import (
        maintenance as _maintenance_mod,
    )
    from .tools import (
        recall as _recall_mod,
    )
    from .tools import (
        recall_filtered as _recall_filtered_mod,
    )
    from .tools import (
        reflect as _reflect_mod,
    )
    from .tools import (
        reindex as _reindex_mod,
    )
    from .tools import (
        remember as _remember_mod,
    )
    from .tools import (
        stats as _stats_mod,
    )
    from .transport.mcp_sse import build_mcp_server

    # Stdio is a single-user local subprocess launched by the MCP client
    # (Claude Desktop, VS Code, Cursor, etc). There is no network exposure,
    # so the HTTP API_KEY check is meaningless here. Synthesize a local-only
    # key if the user hasn't set one, so first-run install is zero-config.
    if not os.environ.get("API_KEY") and not os.environ.get("API_KEYS"):
        os.environ["API_KEY"] = "stdio-local"
        log.info("No API_KEY set; using stdio-local (single-user stdio mode)")

    # Default store/artifacts to ~/.recall/ so they don't litter the cwd
    # the MCP client happened to launch us from.
    _home_recall = os.path.join(os.path.expanduser("~"), ".recall")
    os.environ.setdefault("STORE_DIR", os.path.join(_home_recall, "store"))
    os.environ.setdefault("ARTIFACTS_DIR", os.path.join(_home_recall, "artifacts"))
    os.environ.setdefault("REPO_DIR", os.path.join(_home_recall, "repo"))
    os.environ.setdefault("PREBUILT_DIR", os.path.join(_home_recall, "prebuilt-index"))

    cfg = Config.from_env()

    # Propagate config into tool modules (same as HTTP path)
    for mod in (
        _recall_mod,
        _recall_filtered_mod,
        _remember_mod,
        _reindex_mod,
        _stats_mod,
        _reflect_mod,
        _checkpoint_mod,
        _coordinate_mod,
        _maintenance_mod,
    ):
        mod.set_config(cfg)

    # Make sure dirs exist
    for d in (cfg.store_dir, cfg.artifacts_dir, cfg.repo_dir):
        os.makedirs(d, exist_ok=True)

    # Init embedder + summarizer + store synchronously (stdio clients want
    # tool calls to work on the first request — no background threading).
    try:
        embedder = make_embedder_from_env()
    except Exception:
        log.exception("Embedder init failed; using bundled default")
        from .embedder import DefaultChromaEmbedder

        embedder = DefaultChromaEmbedder()

    try:
        init_summarizer(make_summarizer_from_env())
    except Exception:
        from .summarizer import NoopSummarizer
        from .summarizer import init_summarizer as _is

        _is(NoopSummarizer())

    init_store(cfg.store_dir, cfg.collection_name, embedder=embedder)
    log.info("Recall MCP stdio ready. Store: %s", cfg.store_dir)

    # Hand off to FastMCP — it owns stdin/stdout from here.
    mcp = build_mcp_server(name="recall")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

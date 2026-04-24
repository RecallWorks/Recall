# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | env-driven config | prev: NEW
"""Configuration — all settings come from environment variables.

Defaults are neutral (./data/...) so a fresh `docker run` works without
Azure-specific paths. Operators override via env vars or .env file.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

log = logging.getLogger("recall.config")


@dataclass
class Config:
    # --- API key auth ---------------------------------------------------
    # Per-user keys: JSON map {"user_name": "their_key", ...}
    # Falls back to single API_KEY for single-user setups.
    api_keys: dict[str, str] = field(default_factory=dict)  # key -> user_name

    # --- Storage paths --------------------------------------------------
    # ChromaDB lives on local ephemeral disk (SQLite locking deadlocks on SMB).
    store_dir: str = "./data/store"
    # Durable snapshot target. start.py copies prebuilt_dir -> store_dir on boot.
    prebuilt_dir: str = "./data/prebuilt-index"
    # Persistent artifacts (.md files for remember/reflect/checkpoint/etc).
    # Re-indexed into the store on startup.
    artifacts_dir: str = "./data/artifacts"
    collection_name: str = "recall_memory"

    # --- Optional git sync of an external knowledge repo ---------------
    git_repo_url: str = ""
    git_token: str = ""
    repo_dir: str = "./data/repo"
    index_dirs: list[str] = field(default_factory=lambda: ["knowledge", "docs"])
    file_extensions: list[str] = field(default_factory=lambda: [".md", ".txt"])

    # --- Chunking -------------------------------------------------------
    chunk_size: int = 1500
    chunk_overlap: int = 200

    # --- HTTP transport -------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8787

    # --- Health gate ----------------------------------------------------
    # If reindex finishes but chunk count is below this, /health returns 503.
    # 0 disables the gate.
    min_expected_chunks: int = 0

    # --- Auto-snapshot --------------------------------------------------
    # snapshot_index() fires automatically after this many writes.
    # 0 disables (then operators must call snapshot_index manually).
    auto_snapshot_every: int = 50

    # --- Staleness ------------------------------------------------------
    stale_minutes: int = 10
    checkpoint_ring_max: int = 10

    @classmethod
    def from_env(cls) -> Config:
        """Build a Config from environment variables. Raises RuntimeError if no API key set."""
        c = cls()

        # Auth
        raw = os.environ.get("API_KEYS", "")
        api_key = os.environ.get("API_KEY", "")
        if raw:
            try:
                parsed = json.loads(raw)
                c.api_keys = {v: k for k, v in parsed.items()}
                log.info("Loaded %d user API keys", len(c.api_keys))
            except json.JSONDecodeError as e:
                log.error("API_KEYS is not valid JSON: %s", e)
        if not c.api_keys and api_key:
            c.api_keys = {api_key: "admin"}
            log.info("Using single API_KEY (single-user mode)")
        if not c.api_keys:
            raise RuntimeError("API_KEY or API_KEYS environment variable is required")

        # Paths
        c.store_dir = os.environ.get("STORE_DIR", c.store_dir)
        c.prebuilt_dir = os.environ.get("PREBUILT_DIR", c.prebuilt_dir)
        c.artifacts_dir = os.environ.get("ARTIFACTS_DIR", c.artifacts_dir)
        c.collection_name = os.environ.get("COLLECTION_NAME", c.collection_name)

        # Git
        c.git_repo_url = os.environ.get("GIT_REPO_URL", "")
        c.git_token = os.environ.get("GIT_TOKEN", "")
        c.repo_dir = os.environ.get("REPO_DIR", c.repo_dir)
        c.index_dirs = [
            d.strip()
            for d in os.environ.get("INDEX_DIRS", ",".join(c.index_dirs)).split(",")
            if d.strip()
        ]
        c.file_extensions = [
            e.strip()
            for e in os.environ.get("FILE_EXTENSIONS", ",".join(c.file_extensions)).split(",")
            if e.strip()
        ]

        # Tunables
        c.chunk_size = int(os.environ.get("CHUNK_SIZE", c.chunk_size))
        c.chunk_overlap = int(os.environ.get("CHUNK_OVERLAP", c.chunk_overlap))
        c.host = os.environ.get("HOST", c.host)
        c.port = int(os.environ.get("PORT", c.port))
        c.min_expected_chunks = int(os.environ.get("MIN_EXPECTED_CHUNKS", c.min_expected_chunks))
        c.auto_snapshot_every = int(os.environ.get("AUTO_SNAPSHOT_EVERY", c.auto_snapshot_every))

        return c

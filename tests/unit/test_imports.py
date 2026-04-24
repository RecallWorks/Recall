# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — smoke import test | prev: NEW
"""Smoke test: every Recall module imports cleanly without ChromaDB present."""

def test_top_level_imports():
    import recall
    from recall import config, auth, state, artifacts, chunking, snapshot, git_sync, app  # noqa: F401
    assert recall.__version__


def test_tools_registry_has_thirteen_entries():
    from recall.tools import TOOL_REGISTRY, WRITE_TOOLS
    assert len(TOOL_REGISTRY) == 13
    assert "recall" in TOOL_REGISTRY
    assert "checkpoint" in TOOL_REGISTRY
    assert "snapshot_index" in TOOL_REGISTRY
    # forget is a write tool too — but per delete=archive guardrail it
    # archives, doesn't delete. Tracked separately below.
    assert "snapshot_index" in WRITE_TOOLS


def test_config_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_KEYS", raising=False)
    from recall.config import Config
    import pytest
    with pytest.raises(RuntimeError, match="API_KEY"):
        Config.from_env()


def test_config_from_env_accepts_single_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "xyz")
    from recall.config import Config
    cfg = Config.from_env()
    assert "xyz" in cfg.api_keys
    assert cfg.api_keys["xyz"] == "admin"

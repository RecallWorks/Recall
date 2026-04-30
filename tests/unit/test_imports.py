# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — smoke import test | prev: NEW
"""Smoke test: every Recall module imports cleanly without ChromaDB present."""


def test_top_level_imports():
    import recall
    from recall import (  # noqa: F401
        app,
        artifacts,
        auth,
        chunking,
        config,
        git_sync,
        snapshot,
        state,
    )

    assert recall.__version__


def test_tools_registry_has_fourteen_entries():
    from recall.tools import TOOL_REGISTRY, WRITE_TOOLS

    # 13 originals + answer (2026-04-26) + recall_filtered + backfill_epoch
    # (2026-04-27 b1c4) + 6 multi-agent coordination tools (2026-04-30 a3f7
    # v0.5.0 wedge: claim/release/who_has/claims/handoff/pulse_others).
    assert len(TOOL_REGISTRY) == 22
    assert "recall" in TOOL_REGISTRY
    assert "recall_filtered" in TOOL_REGISTRY
    assert "answer" in TOOL_REGISTRY
    assert "checkpoint" in TOOL_REGISTRY
    assert "snapshot_index" in TOOL_REGISTRY
    assert "backfill_epoch" in TOOL_REGISTRY
    # Coordination tools
    for t in ("claim", "release", "who_has", "claims", "handoff", "pulse_others"):
        assert t in TOOL_REGISTRY, f"{t} missing from TOOL_REGISTRY"
    # forget is a write tool too — but per delete=archive guardrail it
    # archives, doesn't delete. Tracked separately below.
    assert "snapshot_index" in WRITE_TOOLS
    assert "backfill_epoch" in WRITE_TOOLS
    assert "claim" in WRITE_TOOLS
    assert "release" in WRITE_TOOLS
    assert "handoff" in WRITE_TOOLS


def test_config_from_env_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_KEYS", raising=False)
    import pytest

    from recall.config import Config

    with pytest.raises(RuntimeError, match="API_KEY"):
        Config.from_env()


def test_config_from_env_accepts_single_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "xyz")
    from recall.config import Config

    cfg = Config.from_env()
    assert "xyz" in cfg.api_keys
    assert cfg.api_keys["xyz"] == "admin"

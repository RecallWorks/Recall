# @wbx-modified copilot-a3f7 | 2026-04-30 01:05 MTN | v0.1 | tests for multi-agent coordination tools | prev: NEW
"""Tests for coordinate.py — multi-agent coordination primitives.

Uses the same FakeStore harness as test_tools.py.
"""

from __future__ import annotations

import json
import time

import pytest
from fakestore import install

from recall.config import Config
from recall.tools import coordinate as coord


@pytest.fixture
def cfg(tmp_path):
    c = Config()
    c.store_dir = str(tmp_path / "store")
    c.prebuilt_dir = str(tmp_path / "prebuilt")
    c.artifacts_dir = str(tmp_path / "artifacts")
    c.auto_snapshot_every = 0
    return c


@pytest.fixture
def store(monkeypatch, cfg):
    fake = install(monkeypatch)
    coord.set_config(cfg)
    return fake


# ---- claim --------------------------------------------------------------


def test_claim_requires_hex_agent(store):
    out = json.loads(coord.claim(resource="src/foo.py", agent=""))
    assert out["status"] == "error"


def test_claim_acquires_when_free(store):
    out = json.loads(coord.claim(resource="src/foo.py", agent="a3f7"))
    assert out["status"] == "claimed"
    assert out["agent"] == "a3f7"
    assert out["ttl_seconds"] == 600


def test_claim_blocks_when_held_by_another(store):
    coord.claim(resource="src/foo.py", agent="a3f7", note="refactor")
    out = json.loads(coord.claim(resource="src/foo.py", agent="b1c4"))
    assert out["status"] == "blocked"
    assert out["held_by"] == "a3f7"
    assert out["note"] == "refactor"
    assert out["ttl_remaining_seconds"] > 0


def test_claim_self_renewal_succeeds(store):
    coord.claim(resource="src/foo.py", agent="a3f7", ttl_seconds=60)
    out = json.loads(coord.claim(resource="src/foo.py", agent="a3f7", ttl_seconds=120))
    assert out["status"] == "claimed"


def test_claim_rejects_bad_ttl(store):
    out = json.loads(coord.claim(resource="x", agent="a3f7", ttl_seconds=0))
    assert out["status"] == "error"
    out = json.loads(coord.claim(resource="x", agent="a3f7", ttl_seconds=999_999))
    assert out["status"] == "error"


# ---- expiry -------------------------------------------------------------


def test_expired_claim_does_not_block(store, monkeypatch):
    coord.claim(resource="src/foo.py", agent="a3f7", ttl_seconds=1)
    # Advance the clock past the TTL.
    monkeypatch.setattr(coord, "_now_epoch", lambda: time.time() + 5)
    out = json.loads(coord.claim(resource="src/foo.py", agent="b1c4"))
    assert out["status"] == "claimed"
    assert out["agent"] == "b1c4"


# ---- who_has ------------------------------------------------------------


def test_who_has_returns_null_when_free(store):
    out = json.loads(coord.who_has("src/free.py"))
    assert out["held_by"] is None


def test_who_has_returns_holder(store):
    coord.claim(resource="src/foo.py", agent="a3f7", note="hi")
    out = json.loads(coord.who_has("src/foo.py"))
    assert out["held_by"] == "a3f7"
    assert out["note"] == "hi"


# ---- release ------------------------------------------------------------


def test_release_unblocks_resource(store):
    coord.claim(resource="src/foo.py", agent="a3f7")
    out = json.loads(coord.release(resource="src/foo.py", agent="a3f7"))
    assert out["status"] == "released"
    # Now b1c4 can claim it.
    out2 = json.loads(coord.claim(resource="src/foo.py", agent="b1c4"))
    assert out2["status"] == "claimed"


def test_release_not_held(store):
    out = json.loads(coord.release(resource="src/never.py", agent="a3f7"))
    assert out["status"] == "not_held"


def test_release_archives_does_not_delete(store):
    coord.claim(resource="src/foo.py", agent="a3f7")
    pre_count = store.count()
    coord.release(resource="src/foo.py", agent="a3f7")
    # Soft-archive: row still exists with archived=True
    assert store.count() == pre_count
    rows = list(store.rows.values())
    assert any(r.metadata.get("archived") for r in rows)


# ---- claims (list) ------------------------------------------------------


def test_claims_lists_active_only(store, monkeypatch):
    coord.claim(resource="a.py", agent="a3f7", ttl_seconds=600)
    coord.claim(resource="b.py", agent="b1c4", ttl_seconds=600)
    coord.claim(resource="c.py", agent="c4a1", ttl_seconds=1)
    monkeypatch.setattr(coord, "_now_epoch", lambda: time.time() + 5)
    out = json.loads(coord.claims())
    # c.py expired; a.py and b.py still active
    held = sorted(c["resource"] for c in out["claims"])
    assert held == ["a.py", "b.py"]


# ---- handoff ------------------------------------------------------------


def test_handoff_writes_record(store):
    out = json.loads(
        coord.handoff(
            to_agent="b1c4",
            from_agent="a3f7",
            intent="finish the refactor",
            files="src/foo.py,src/bar.py",
            context="tests pass; need to update README",
        )
    )
    assert out["status"] == "delivered"
    assert out["to"] == "b1c4"
    rows = [r for r in store.rows.values() if r.metadata.get("type") == "handoff"]
    assert len(rows) == 1
    md = rows[0].metadata
    assert md["from_agent"] == "a3f7" and md["to_agent"] == "b1c4"


def test_handoff_requires_hex_agents(store):
    out = json.loads(
        coord.handoff(to_agent="bad", from_agent="a3f7", intent="x")
    )
    assert out["status"] == "error"


# ---- pulse_others -------------------------------------------------------


def test_pulse_others_excludes_self(store):
    # Seed three checkpoints from three agents.
    import time as _time

    from recall.tools import checkpoint as cp_mod

    cp_mod.set_config(coord._config())
    cp_mod.checkpoint(intent="i1", established="e", pursuing="p", open_questions="o", session="a3f7")
    _time.sleep(0.01)  # checkpoint IDs hash from ts; avoid id collision
    cp_mod.checkpoint(intent="i2", established="e", pursuing="p", open_questions="o", session="b1c4")
    _time.sleep(0.01)
    cp_mod.checkpoint(intent="i3", established="e", pursuing="p", open_questions="o", session="c4a1")
    out = json.loads(coord.pulse_others(self_agent="a3f7"))
    agents = sorted(c["agent"] for c in out["checkpoints"])
    assert "a3f7" not in agents
    assert set(agents) == {"b1c4", "c4a1"}

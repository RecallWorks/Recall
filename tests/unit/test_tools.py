# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — write-tool tests against in-memory FakeStore | prev: NEW
import pytest

from recall.config import Config
from recall.state import S
from recall.tools import remember as remember_mod
from recall.tools import reflect as reflect_mod
from recall.tools import checkpoint as checkpoint_mod
from recall.tools import stats as stats_mod
from recall.tools import recall as recall_mod
from fakestore import install


@pytest.fixture
def cfg(tmp_path):
    c = Config()
    c.store_dir = str(tmp_path / "store")
    c.prebuilt_dir = str(tmp_path / "prebuilt")
    c.artifacts_dir = str(tmp_path / "artifacts")
    c.auto_snapshot_every = 0  # disable for tests
    return c


@pytest.fixture
def store(monkeypatch, cfg):
    fake = install(monkeypatch)
    for mod in (remember_mod, reflect_mod, checkpoint_mod, stats_mod, recall_mod):
        mod.set_config(cfg)
    # reset shared state
    S.checkpoint_ring.clear()
    S.last_checkpoint_ts = None
    S.writes_since_snapshot = 0
    return fake


def test_remember_writes_chunk(store):
    out = remember_mod.remember(content="hello world", source="agent-test", tags="t1")
    assert "Stored" in out
    assert store.count() == 1
    row = next(iter(store.rows.values()))
    assert row.metadata["type"] == "observation"
    assert row.metadata["tags"] == "t1"


def test_reflect_requires_hex_session(store):
    out = reflect_mod.reflect(
        domain="d", hypothesis="h", reasoning="r", result="SUCCESS x",
        revised_belief="rb", next_time="nt", confidence=0.5, session="",
    )
    assert "ERROR" in out
    assert store.count() == 0


def test_reflect_writes_with_hex(store):
    out = reflect_mod.reflect(
        domain="d", hypothesis="h", reasoning="r", result="SUCCESS x",
        revised_belief="rb", next_time="nt", confidence=0.5, session="c4a1",
    )
    assert "Reasoning stored" in out
    assert store.count() == 1
    row = next(iter(store.rows.values()))
    assert row.metadata["type"] == "reasoning"
    assert row.metadata["session"] == "c4a1"


def test_checkpoint_updates_ring_and_timestamp(store):
    out = checkpoint_mod.checkpoint(
        intent="i", established="e", pursuing="p", open_questions="q",
        session="c4a1", domain="dev",
    )
    assert "Checkpoint stored" in out
    assert len(S.checkpoint_ring) == 1
    assert S.last_checkpoint_ts is not None


def test_anti_pattern_writes(store):
    out = reflect_mod.anti_pattern(
        domain="d", temptation="t", why_wrong="w", signature="s",
        instead="i", session="c4a1",
    )
    assert "Anti-pattern stored" in out
    row = next(iter(store.rows.values()))
    assert row.metadata["type"] == "anti_pattern"


def test_session_close_writes(store):
    out = reflect_mod.session_close(
        session_id="c4a1", reasoning_changed="rc", do_differently="dd",
        still_uncertain="su", temptations="tx",
    )
    assert "Session reflection stored" in out
    row = next(iter(store.rows.values()))
    assert row.metadata["type"] == "reflection"


def test_forget_archives_does_not_delete(store):
    remember_mod.remember(content="foo", source="src-a")
    remember_mod.remember(content="bar", source="src-a")
    remember_mod.remember(content="baz", source="src-b")
    assert store.count() == 3
    out = stats_mod.forget("src-a")
    assert "Archived 2" in out
    # Per delete=archive guardrail: row count unchanged.
    assert store.count() == 3
    archived = [r for r in store.rows.values() if r.metadata.get("archived")]
    assert len(archived) == 2


def test_recall_finds_observation(store):
    remember_mod.remember(content="needle in haystack", source="src", tags="")
    out = recall_mod.recall(query="needle", n=5, type="observation")
    assert "needle in haystack" in out


def test_memory_stats_empty(store):
    out = stats_mod.memory_stats()
    assert "empty" in out.lower()


def test_memory_stats_populated(store):
    remember_mod.remember(content="x", source="src-1")
    out = stats_mod.memory_stats()
    assert "Total chunks: 1" in out

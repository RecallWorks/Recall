# @wbx-modified copilot-b1c4 | 2026-04-27 19:30 MTN | v1.0 | tests for recall_filtered + backfill_epoch | prev: NEW
"""Tests for recall_filtered + backfill_epoch."""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import pytest

from tests.fakestore import install


def _seed(fake, epoch: float | None = None, **meta):
    """Add a row with given metadata."""
    base = {
        "source": "test",
        "chunk_index": 0,
        "indexed_at": datetime.now().isoformat(),
        "type": "observation",
    }
    if epoch is not None:
        base["indexed_at_epoch"] = epoch
    base.update(meta)
    rid = f"id-{len(fake.rows) + 1}"
    fake.upsert([rid], [f"doc {rid}"], [base])
    return rid


def test_parse_since_relative():
    from recall.tools.recall_filtered import _parse_since

    ep, iso = _parse_since("7d")
    assert ep is not None and iso is not None
    assert ep < time.time()

    ep24, _ = _parse_since("24h")
    assert ep24 is not None
    assert ep24 > _parse_since("7d")[0]


def test_parse_since_invalid():
    from recall.tools.recall_filtered import _parse_since

    assert _parse_since("garbage") == (None, None)
    assert _parse_since("") == (None, None)


def test_build_filter_combinations():
    from recall.tools.recall_filtered import _build_filter

    assert _build_filter("all", "", "", "", None, None) is None
    assert _build_filter("anti_pattern", "", "", "", None, None) == {"type": "anti_pattern"}

    f = _build_filter("anti_pattern", "icewhisperer", "", "", None, None)
    assert f == {"$and": [{"type": "anti_pattern"}, {"domain": "icewhisperer"}]}

    f = _build_filter("all", "", "a3f7", "", None, None)
    assert "$or" in f
    assert {"session": "a3f7"} in f["$or"]
    assert {"session": "copilot-a3f7"} in f["$or"]

    f = _build_filter("all", "", "", "", 1000.0, "x")
    assert f == {"indexed_at_epoch": {"$gte": 1000.0}}


def test_recall_filtered_empty_store(monkeypatch):
    install(monkeypatch)
    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(query="x")
    assert payload["results"] == []
    assert "empty" in payload["result"].lower()


def test_recall_filtered_by_type(monkeypatch):
    fake = install(monkeypatch)
    _seed(fake, type="anti_pattern", domain="d1", source="anti-pattern/d1")
    _seed(fake, type="reflection", domain="d1", source="reflection/d1")
    _seed(fake, type="observation")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(type="anti_pattern")
    assert len(payload["results"]) == 1
    assert payload["results"][0]["type"] == "anti_pattern"


def test_recall_filtered_since_epoch_only(monkeypatch):
    fake = install(monkeypatch)
    now = time.time()
    _seed(fake, epoch=now - 86400 * 10, source="old")  # 10 days ago
    _seed(fake, epoch=now - 3600, source="recent")  # 1 hr ago
    _seed(fake, epoch=None, source="legacy")  # no epoch -- excluded by since=

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(since="7d")
    sources = {r["source"] for r in payload["results"]}
    assert "recent" in sources
    assert "old" not in sources
    assert "legacy" not in sources  # missing epoch -> excluded


def test_recall_filtered_session_normalization(monkeypatch):
    fake = install(monkeypatch)
    _seed(fake, session="a3f7", source="bare-session")
    _seed(fake, session="copilot-a3f7", source="prefixed-session")
    _seed(fake, session="b1c4", source="other")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(session="a3f7")
    sources = {r["source"] for r in payload["results"]}
    assert sources == {"bare-session", "prefixed-session"}


def test_recall_filtered_source_prefix(monkeypatch):
    fake = install(monkeypatch)
    _seed(fake, source="checkpoint/a3f7")
    _seed(fake, source="checkpoint/b1c4")
    _seed(fake, source="reflection/a3f7")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(source_prefix="checkpoint/")
    sources = {r["source"] for r in payload["results"]}
    assert sources == {"checkpoint/a3f7", "checkpoint/b1c4"}


def test_recall_filtered_envelope_shape(monkeypatch):
    fake = install(monkeypatch)
    _seed(fake, type="observation")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(type="observation")
    assert "result" in payload
    assert "results" in payload
    assert isinstance(payload["results"], list)
    if payload["results"]:
        row = payload["results"][0]
        for k in ("rank", "distance", "type", "source", "domain", "confidence", "text"):
            assert k in row


def test_recall_filtered_invalid_type(monkeypatch):
    install(monkeypatch)
    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(type="bogus")
    assert "error" in payload
    assert payload["results"] == []


def test_backfill_epoch_idempotent(monkeypatch):
    fake = install(monkeypatch)
    iso = (datetime.now() - timedelta(hours=2)).isoformat()
    fake.upsert(
        ["a", "b", "c"],
        ["doc a", "doc b", "doc c"],
        [
            {"source": "x", "chunk_index": 0, "indexed_at": iso, "type": "observation"},
            {"source": "y", "chunk_index": 0, "indexed_at": iso, "type": "observation"},
            {"source": "z", "chunk_index": 0, "indexed_at": iso, "type": "observation"},
        ],
    )

    from recall.tools.backfill import backfill_epoch

    r1 = backfill_epoch(start=0, batch_size=2)
    assert "fixed=2" in r1
    assert "next=2" in r1

    r2 = backfill_epoch(start=2, batch_size=2)
    assert "done" in r2
    assert "fixed=1" in r2

    # Idempotent re-run: nothing left to fix.
    r3 = backfill_epoch(start=0, batch_size=10)
    assert "done" in r3
    assert "fixed=0" in r3
    assert "skipped=3" in r3

    # Verify all rows now have indexed_at_epoch.
    for r in fake.rows.values():
        assert isinstance(r.metadata.get("indexed_at_epoch"), float)


def test_backfill_no_delete(monkeypatch):
    """Critical: backfill_epoch is delete-free (per delete=archive guardrail)."""
    fake = install(monkeypatch)
    iso = datetime.now().isoformat()
    for i in range(5):
        fake.upsert(
            [f"id{i}"],
            [f"doc{i}"],
            [{"source": "x", "chunk_index": 0, "indexed_at": iso, "type": "observation"}],
        )
    before = fake.count()

    from recall.tools.backfill import backfill_epoch

    backfill_epoch(start=0, batch_size=10)
    assert fake.count() == before


def test_source_family():
    from recall.tools.recall_filtered import _source_family

    # 4+ dotted segments → first 4 segments (SDK doc spam collapse)
    assert _source_family("EllieMae.Encompass.Configuration.CustomField.md") == "EllieMae.Encompass.Configuration.CustomField"
    assert _source_family("path/to/EllieMae.Encompass.BusinessRules.Rule.Foo.md") == "EllieMae.Encompass.BusinessRules.Rule"
    # <4 dotted → parent dir
    assert _source_family("sdk-reference/Foo/Bar.md") == "Foo"
    assert _source_family("checkpoint\\a3f7\\note.md") == "a3f7"
    assert _source_family("/data/repo/encompass/forum/topic.md") == "forum"
    assert _source_family("admin-settings/04-fields.md") == "admin-settings"
    assert _source_family("standalone") == "standalone"
    assert _source_family("") == ""
    assert _source_family("/") == ""


def test_low_confidence_signal():
    from recall.tools.recall_filtered import _low_confidence

    # Trigger A — single family with n>=4
    rows_single_fam = [
        {"distance": 0.10, "source": "sdk/Foo/A.md"},
        {"distance": 0.15, "source": "sdk/Foo/B.md"},
        {"distance": 0.20, "source": "sdk/Foo/C.md"},
        {"distance": 0.25, "source": "sdk/Foo/D.md"},
    ]
    assert _low_confidence(rows_single_fam) is True

    # Multi-family low-distance — not low confidence
    rows_multi = [
        {"distance": 0.10, "source": "sdk/Foo/A.md"},
        {"distance": 0.11, "source": "forum/topic.md"},
        {"distance": 0.12, "source": "admin/settings.md"},
        {"distance": 0.13, "source": "knowledge/x.md"},
    ]
    assert _low_confidence(rows_multi) is False

    # Trigger B — tight cluster + high mean (multi-family but all weak)
    rows_tight_high = [
        {"distance": 0.31, "source": "a/x.md"},
        {"distance": 0.32, "source": "b/y.md"},
        {"distance": 0.33, "source": "c/z.md"},
    ]
    assert _low_confidence(rows_tight_high) is True

    # Tight but low mean — strong signal, not low confidence
    rows_tight_low = [
        {"distance": 0.10, "source": "a/x.md"},
        {"distance": 0.11, "source": "b/y.md"},
        {"distance": 0.12, "source": "c/z.md"},
    ]
    assert _low_confidence(rows_tight_low) is False

    # Wide spread — strong differentiation, not low confidence
    rows_wide = [
        {"distance": 0.10, "source": "a/x.md"},
        {"distance": 0.25, "source": "b/y.md"},
        {"distance": 0.40, "source": "c/z.md"},
    ]
    assert _low_confidence(rows_wide) is False

    # Too few rows
    assert _low_confidence([{"distance": 0.50, "source": "a/x.md"}]) is False

    # No distances + multi-family + n<4 — not low confidence
    assert _low_confidence(
        [{"distance": None, "source": "a/x.md"}, {"distance": None, "source": "b/y.md"}]
    ) is False


def test_diversify_rebalances_families():
    from recall.tools.recall_filtered import _diversify

    # 5 from family A, 2 from family B; without diversity, top-3 = all A.
    rows = [
        {"rank": 1, "source": "A/1", "distance": 0.31},
        {"rank": 2, "source": "A/2", "distance": 0.32},
        {"rank": 3, "source": "A/3", "distance": 0.33},
        {"rank": 4, "source": "A/4", "distance": 0.34},
        {"rank": 5, "source": "B/1", "distance": 0.35},
        {"rank": 6, "source": "A/5", "distance": 0.36},
        {"rank": 7, "source": "B/2", "distance": 0.37},
    ]
    out = _diversify(rows, n=3, min_families=2)
    families = {r["source"].split("/")[0] for r in out[:3]}
    assert "B" in families  # B got promoted into top-3
    assert out[0]["source"] == "A/1"  # first pick still preserves rank 1
    assert out[1]["source"] == "B/1"  # round-robin picks B next
    # Ranks rewritten
    assert out[0]["rank"] == 1
    assert out[1]["rank"] == 2


def test_diversify_skips_when_homogeneous():
    from recall.tools.recall_filtered import _diversify

    rows = [
        {"rank": 1, "source": "A/1", "distance": 0.31},
        {"rank": 2, "source": "A/2", "distance": 0.32},
    ]
    out = _diversify(rows, n=2, min_families=2)
    # Only one family -> returns as-is
    assert out[0]["source"] == "A/1"
    assert out[1]["source"] == "A/2"


def test_recall_filtered_diversity_param(monkeypatch):
    fake = install(monkeypatch)
    for i in range(4):
        _seed(fake, source=f"sdk-reference/Foo/Bar{i}.md", type="document")
    _seed(fake, source="forum/topic_5140.md", type="document")
    _seed(fake, source="forum/topic_9001.md", type="document")

    from recall.tools.recall_filtered import _recall_filtered_structured

    # diversity=True + compute_confidence=True → both fields populated
    payload = _recall_filtered_structured(
        n=3, diversity=True, min_diversity=2, compute_confidence=True
    )
    assert "low_confidence" in payload
    assert "families" in payload
    assert isinstance(payload["families"], list)


def test_recall_filtered_compute_confidence_default_off(monkeypatch):
    """Default behavior (compute_confidence=False) omits low_confidence/families."""
    fake = install(monkeypatch)
    _seed(fake, type="observation")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(type="observation")
    assert "low_confidence" not in payload
    assert "families" not in payload
    # Envelope still has core fields
    assert "result" in payload
    assert "results" in payload


def test_recall_filtered_compute_confidence_opt_in(monkeypatch):
    fake = install(monkeypatch)
    _seed(fake, type="observation", source="forum/x.md")

    from recall.tools.recall_filtered import _recall_filtered_structured

    payload = _recall_filtered_structured(type="observation", compute_confidence=True)
    assert "low_confidence" in payload
    assert "families" in payload
    assert isinstance(payload["low_confidence"], bool)
    assert isinstance(payload["families"], list)

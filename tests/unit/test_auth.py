# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — auth tests | prev: NEW
import pytest

from recall.auth import BadSession, require_hex, verify_key


def test_verify_key_match():
    keys = {"abc123": "alice"}
    assert verify_key(keys, "abc123") == "alice"


def test_verify_key_no_match():
    keys = {"abc123": "alice"}
    assert verify_key(keys, "wrong") is None


def test_verify_key_empty():
    assert verify_key({}, "anything") is None


@pytest.mark.parametrize("good", ["b8d2", "c4a1", "0000", "ffff", "copilot-b8d2"])
def test_require_hex_accepts(good):
    assert require_hex(good, "session") == good


@pytest.mark.parametrize("bad", ["", "g000", "B8D2", "12345", "b8d", "session-1"])
def test_require_hex_rejects(bad):
    with pytest.raises(BadSession):
        require_hex(bad, "session")

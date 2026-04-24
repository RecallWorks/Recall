# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — chunking tests | prev: NEW
from recall.chunking import chunk_text


def test_chunk_text_short():
    out = chunk_text("hello", "src", chunk_size=10, chunk_overlap=2)
    assert len(out) == 1
    assert out[0]["text"] == "hello"
    assert out[0]["source"] == "src"
    assert out[0]["chunk_index"] == 0


def test_chunk_text_overlap():
    out = chunk_text("0123456789ABCDEFGHIJ", "src", chunk_size=8, chunk_overlap=2)
    # step = 6, len = 20: starts at 0, 6, 12, 18 → 4 chunks
    assert len(out) == 4
    assert out[0]["text"] == "01234567"
    assert out[1]["text"] == "6789ABCD"
    assert out[3]["text"] == "IJ"


def test_chunk_ids_are_stable():
    a = chunk_text("hello world", "src", chunk_size=20, chunk_overlap=0)
    b = chunk_text("hello world", "src", chunk_size=20, chunk_overlap=0)
    assert a[0]["id"] == b[0]["id"]

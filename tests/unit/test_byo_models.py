# @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: tests for embedder + summarizer factories
"""Unit tests for BYO embedder + summarizer factories.

Network-free: only exercises the env-var routing and noop/default sentinels.
The OpenAI/Ollama branches are covered by import-error paths.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for k in list(os.environ):
        if k.startswith("RECALL_") or k in ("OPENAI_API_KEY",):
            monkeypatch.delenv(k, raising=False)
    yield


def test_embedder_default_when_unset(clean_env: None) -> None:
    from recall.embedder import DefaultChromaEmbedder, make_embedder_from_env

    e = make_embedder_from_env()
    assert isinstance(e, DefaultChromaEmbedder)
    assert e.name == "default"


def test_embedder_default_explicit(monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    from recall.embedder import DefaultChromaEmbedder, make_embedder_from_env

    monkeypatch.setenv("RECALL_EMBEDDER", "default")
    assert isinstance(make_embedder_from_env(), DefaultChromaEmbedder)


def test_embedder_unknown_raises(monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    from recall.embedder import make_embedder_from_env

    monkeypatch.setenv("RECALL_EMBEDDER", "nonsense")
    with pytest.raises(RuntimeError, match="Unknown RECALL_EMBEDDER"):
        make_embedder_from_env()


def test_summarizer_noop_when_unset(clean_env: None) -> None:
    from recall.summarizer import NoopSummarizer, make_summarizer_from_env

    s = make_summarizer_from_env()
    assert isinstance(s, NoopSummarizer)
    assert s.name == "noop"


def test_summarizer_noop_passthrough(clean_env: None) -> None:
    from recall.summarizer import NoopSummarizer

    s = NoopSummarizer()
    text = "this is a long narrative " * 50
    assert s.summarize(text) == text
    assert s.summarize(text, max_words=10) == text  # noop ignores max_words


def test_summarizer_unknown_raises(monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    from recall.summarizer import make_summarizer_from_env

    monkeypatch.setenv("RECALL_SUMMARIZER", "nonsense")
    with pytest.raises(RuntimeError, match="Unknown RECALL_SUMMARIZER"):
        make_summarizer_from_env()


def test_get_summarizer_returns_noop_if_uninit() -> None:
    # init_summarizer() may not have been called in test isolation.
    from recall import summarizer as sm

    # Force-clear the singleton.
    sm._summarizer = None
    s = sm.get_summarizer()
    assert isinstance(s, sm.NoopSummarizer)


def test_init_summarizer_swaps_singleton() -> None:
    from recall import summarizer as sm

    sentinel = sm.NoopSummarizer()
    sm.init_summarizer(sentinel)
    assert sm.get_summarizer() is sentinel

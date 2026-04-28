# @wbx-modified copilot-a3f7·MTN | 2026-04-26 01:25 MTN | v0.1 | answer tool tests w/ FakeLLM (no network) | prev: original
"""Unit tests for the synthesis (answer) tool.

The tests inject a FakeLLM via `set_provider`, so no Azure OpenAI SDK or
network access is required. They prove the tool:
  - retrieves the right number of chunks,
  - builds the prompt with numbered Sources,
  - returns valid JSON with answer + sources + model,
  - degrades cleanly (empty store, blank question, provider failure).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import pytest
from fakestore import install

from recall.config import Config
from recall.tools import answer as answer_mod
from recall.tools import remember as remember_mod


@dataclass
class FakeLLM:
    reply: str = "synthesized answer [1]"
    last_system: str = ""
    last_user: str = ""
    last_max_tokens: int = 0
    deployment: str = "fake-llm"
    raise_on_call: Exception | None = None
    calls: int = 0

    def complete(self, *, system: str, user: str, max_tokens: int = 800) -> str:
        self.calls += 1
        self.last_system = system
        self.last_user = user
        self.last_max_tokens = max_tokens
        if self.raise_on_call is not None:
            raise self.raise_on_call
        return self.reply


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
    remember_mod.set_config(cfg)
    answer_mod.set_config(cfg)
    answer_mod.set_provider(None)  # reset provider between tests
    return fake


def test_answer_blank_question_errors(store):
    out = json.loads(answer_mod.answer(question="   "))
    assert out.get("error") == "question is required"


def test_answer_empty_store_errors(store):
    answer_mod.set_provider(FakeLLM())
    out = json.loads(answer_mod.answer(question="anything"))
    assert "error" in out
    assert "empty" in out["error"]


def test_answer_returns_synthesis_with_sources(store):
    remember_mod.remember(content="Loan folder paths use forward slashes only.", source="kb/folders.md", tags="")
    remember_mod.remember(content="The /v3 path replaced /v1 for most settings endpoints.", source="kb/api.md", tags="")
    llm = FakeLLM(reply="Use forward slashes [1]. Settings moved to /v3 [2].")
    answer_mod.set_provider(llm)

    raw = answer_mod.answer(question="how do folder paths work and where do settings live?", n=4)
    out = json.loads(raw)

    assert out["answer"].startswith("Use forward slashes")
    assert out["model"] == "fake-llm"
    assert out["chunks_used"] >= 1
    assert isinstance(out["sources"], list)
    assert all({"n", "source", "snippet"} <= s.keys() for s in out["sources"])
    # Prompt was built with a numbered context block.
    assert "Supporting context" in llm.last_user
    assert "chunk 1" in llm.last_user


def test_answer_clamps_n_to_20(store):
    for i in range(5):
        remember_mod.remember(content=f"chunk {i}", source=f"src{i}", tags="")
    llm = FakeLLM()
    answer_mod.set_provider(llm)
    out = json.loads(answer_mod.answer(question="q", n=999))
    # only 5 chunks exist; tool must cap n by store size, not crash.
    assert out["chunks_used"] == 5


def test_answer_propagates_provider_failure_as_json_error(store):
    remember_mod.remember(content="hello", source="src", tags="")
    answer_mod.set_provider(FakeLLM(raise_on_call=RuntimeError("boom")))
    out = json.loads(answer_mod.answer(question="q"))
    assert "error" in out
    assert "boom" in out["error"]


def test_answer_passes_max_tokens_to_provider(store):
    remember_mod.remember(content="x", source="src", tags="")
    llm = FakeLLM()
    answer_mod.set_provider(llm)
    answer_mod.answer(question="q", max_tokens=123)
    assert llm.last_max_tokens == 123


def test_answer_registered_in_tool_registry():
    from recall.tools import TOOL_REGISTRY

    assert "answer" in TOOL_REGISTRY
    assert TOOL_REGISTRY["answer"] is answer_mod.answer

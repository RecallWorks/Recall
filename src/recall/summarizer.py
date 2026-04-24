# @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: BYO-LLM summarizer seam (noop/openai/ollama) | prev: NEW
"""Pluggable LLM summarizers.

Used to condense long narrative fields (session reflections, multi-step
checkpoints) into shorter retrievable chunks. Three reference implementations:

  * ``noop`` — return the input unchanged. Default. No network, no model.
  * ``openai`` — chat-completions API (OpenAI / Azure / OpenAI-compatible).
  * ``ollama`` — local Ollama server.

Customers in regulated environments can configure the local backend so the
brain never ships content to a hosted LLM. Customers without an LLM at all
keep the noop default — Recall still works, it just stores raw content.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

log = logging.getLogger("recall.summarizer")

_DEFAULT_PROMPT = (
    "You are a concise technical summarizer. Compress the following content into "
    "at most {max_words} words. Preserve concrete facts, names, IDs, and "
    "decisions. Drop filler. Return only the summary."
)


@runtime_checkable
class Summarizer(Protocol):
    name: str

    def summarize(self, text: str, max_words: int = 120) -> str: ...


class NoopSummarizer:
    """Return the input unchanged. Use when no LLM is available."""

    name = "noop"

    def summarize(self, text: str, max_words: int = 120) -> str:
        return text


class OpenAISummarizer:
    """OpenAI / Azure-OpenAI / OpenAI-compatible chat-completions summarizer."""

    name = "openai"

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        prompt_template: str | None = None,
    ) -> None:
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError("RECALL_SUMMARIZER=openai requires `pip install openai`") from e
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model
        self._prompt = prompt_template or _DEFAULT_PROMPT
        log.info("OpenAISummarizer ready. model=%s base_url=%s", model, base_url or "default")

    def summarize(self, text: str, max_words: int = 120) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._prompt.format(max_words=max_words)},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()


class OllamaSummarizer:
    """Local Ollama chat-completions summarizer."""

    name = "ollama"

    def __init__(
        self,
        model: str,
        endpoint: str = "http://localhost:11434",
        prompt_template: str | None = None,
    ) -> None:
        try:
            import httpx  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError("RECALL_SUMMARIZER=ollama requires `pip install httpx`") from e
        self._httpx = httpx
        self._model = model
        self._endpoint = endpoint.rstrip("/")
        self._prompt = prompt_template or _DEFAULT_PROMPT
        log.info("OllamaSummarizer ready. model=%s endpoint=%s", model, self._endpoint)

    def summarize(self, text: str, max_words: int = 120) -> str:
        with self._httpx.Client(timeout=120.0) as client:
            r = client.post(
                f"{self._endpoint}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": self._prompt.format(max_words=max_words)},
                        {"role": "user", "content": text},
                    ],
                },
            )
            r.raise_for_status()
            return (r.json().get("message", {}).get("content") or "").strip()


def make_summarizer_from_env() -> Summarizer:
    """Build a Summarizer per env vars. Falls back to NoopSummarizer."""
    kind = os.environ.get("RECALL_SUMMARIZER", "noop").lower()
    if kind == "noop":
        return NoopSummarizer()
    if kind == "openai":
        return OpenAISummarizer(
            model=os.environ.get("RECALL_LLM_MODEL", "gpt-4o-mini"),
            api_key=os.environ.get("RECALL_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("RECALL_LLM_BASE_URL") or None,
        )
    if kind == "ollama":
        return OllamaSummarizer(
            model=os.environ.get("RECALL_LLM_MODEL", "llama3.1"),
            endpoint=os.environ.get("RECALL_LLM_ENDPOINT", "http://localhost:11434"),
        )
    raise RuntimeError(f"Unknown RECALL_SUMMARIZER='{kind}'. Use one of: noop, openai, ollama.")


# Module-level lazy singleton — set by app.py at startup.
_summarizer: Summarizer | None = None


def init_summarizer(s: Summarizer) -> None:
    global _summarizer
    _summarizer = s


def get_summarizer() -> Summarizer:
    if _summarizer is None:
        return NoopSummarizer()
    return _summarizer

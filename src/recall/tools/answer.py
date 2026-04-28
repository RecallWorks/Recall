# @wbx-modified copilot-a3f7·MTN | 2026-04-26 01:15 MTN | v0.1 | synthesis tool — recall + LLM + cited answer | prev: original
"""answer — synthesize a cited answer from indexed memory.

Pipeline:
  1. Run a semantic recall against the store (top-N chunks, default 8).
  2. Build a grounded prompt: question + numbered chunks + system rules.
  3. Call the configured LLM provider (default: Azure OpenAI gpt-4o-mini).
  4. Return JSON: {"answer": str, "sources": [{n, source, snippet}]}.

Provider is a Protocol so the substrate stays vendor-neutral. Tests use
FakeLLM. Production wires AzureOpenAIProvider via env (AZURE_OPENAI_*).
The provider is selected lazily on first call so unit tests that never
invoke `answer` don't need the openai SDK installed.
"""
from __future__ import annotations

import json
import logging
import os
import textwrap
from dataclasses import dataclass
from typing import Protocol

from ..config import Config
from ..store import get_store

log = logging.getLogger("recall.answer")


# ---- LLM provider interface ------------------------------------------
class LLMProvider(Protocol):
    """Sync chat completion. Returns the assistant's text reply."""

    def complete(self, *, system: str, user: str, max_tokens: int = 800) -> str: ...


@dataclass
class AzureOpenAIProvider:
    """Azure OpenAI chat-completion provider (gpt-4o-mini default deployment).

    Env required at construction time:
      AZURE_OPENAI_ENDPOINT      — e.g. https://my-aoai.openai.azure.com
      AZURE_OPENAI_API_KEY       — key, OR omit and DefaultAzureCredential is used
      AZURE_OPENAI_DEPLOYMENT    — deployment name (default: gpt-4o-mini)
      AZURE_OPENAI_API_VERSION   — default: 2024-08-01-preview
    """

    endpoint: str
    deployment: str
    api_version: str
    api_key: str | None  # None → use DefaultAzureCredential

    def complete(self, *, system: str, user: str, max_tokens: int = 800) -> str:
        # Lazy import — keeps the SDK out of the unit-test path.
        from openai import AzureOpenAI

        if self.api_key:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider

            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
            client = AzureOpenAI(
                azure_ad_token_provider=token_provider,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )
        resp = client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.2,  # grounded > creative
        )
        return resp.choices[0].message.content or ""


def _provider_from_env() -> LLMProvider:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError(
            "answer: AZURE_OPENAI_ENDPOINT not set. "
            "Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT (and either "
            "AZURE_OPENAI_API_KEY or rely on DefaultAzureCredential)."
        )
    return AzureOpenAIProvider(
        endpoint=endpoint,
        deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY") or None,
    )


# ---- prompt construction ---------------------------------------------
_SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are a senior mortgage-operations colleague answering a question for a
    teammate. You know Encompass administration, loan workflow, disclosures,
    underwriting, secondary, and compliance cold. You speak like a person, not
    a citation engine.

    Output format (RFC-lite — apply EVERY answer):

      **Answer.** One declarative sentence stating the bottom line.

      **Details.** One short paragraph (2-5 sentences) of prose. Confident,
      conversational, no hedging filler. This is where you teach.

      **Steps.** (Include ONLY if the question is procedural — "how do I...",
      "what's the process for..."). Numbered list. One imperative clause per
      step. Do not pad.

      **Watch out.** (Include ONLY if there's a real gotcha — file lock,
      compliance trap, version-specific bug, common mistake). One or two short
      bullets, each starting with the hazard.

    Voice rules:
      - Do NOT say "the Sources say" or "according to the provided
        information." Speak as if you simply know this.
      - Do NOT pepper your reply with inline [1][2][3] markers. The caller
        appends a Sources footer from a structured list.
      - No throat-clearing. No "great question." No "I hope this helps."
      - Bold the four section labels exactly: **Answer.**, **Details.**,
        **Steps.**, **Watch out.** Skip a label if the section doesn't apply.

    Honesty rules:
      - If the supporting context below does not contain the answer, OR the
        question is off-topic for mortgage / Encompass operations, return ONLY
        this single line: "**Answer.** I don't have that in your brain."
        Optionally add one **Details.** sentence pointing at what would need
        to be added. Do NOT invent file numbers, version numbers, API names,
        or regulatory cites.
      - If the context disagrees with itself, surface the disagreement in
        **Details.**; don't silently pick one side.

    The supporting context below is private to this tenant; treat it as the
    authoritative knowledge you are recalling.
    """
).strip()


def _build_user_prompt(question: str, chunks: list[dict]) -> str:
    parts = [f"Question: {question}", "", "Supporting context (from this tenant's brain):"]
    for i, c in enumerate(chunks, start=1):
        src = c.get("source", "unknown")
        body = c.get("text", "").strip()
        parts.append(f"--- chunk {i} (source: {src}) ---")
        parts.append(body)
        parts.append("")
    parts.append(
        "Now answer the colleague's question in your own voice, as prose, "
        "without inline [n] citation markers. If the context above does not "
        "support a confident answer, say \"I don't have that in your brain.\""
    )
    return "\n".join(parts)


# ---- tool entry point -------------------------------------------------
_provider: LLMProvider | None = None
_cfg: Config | None = None


def set_provider(provider: LLMProvider | None) -> None:
    """Tests / alternative providers inject here. None resets to env-default on next call."""
    global _provider
    _provider = provider


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config


def _default_config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def answer(
    question: str,
    n: int = 8,
    type: str = "all",
    max_tokens: int = 800,
    config: Config | None = None,
) -> str:
    """Synthesize a cited answer from indexed memory.

    Args:
        question: Natural-language question.
        n: Number of chunks to retrieve and ground on (default 8, capped 20).
        type: Optional artifact-type filter (matches recall tool).
        max_tokens: LLM completion cap (default 800).
        config: Runtime config. If None, uses module default.

    Returns JSON string: {"answer", "sources", "model", "chunks_used"}.
    On error returns a JSON string with an "error" key (HTTP transport
    still returns 200 — the caller inspects the JSON).
    """
    if config is not None:
        set_config(config)
    else:
        _default_config()
    store = get_store()
    if not question or not question.strip():
        return json.dumps({"error": "question is required"})
    n = min(max(int(n), 1), 20)
    if store.count() == 0:
        return json.dumps({"error": "memory is empty — run reindex first"})
    where = {"type": type} if type != "all" else None
    n = min(n, store.count())
    raw = store.query(query_texts=[question], n_results=n, where=where)
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    if not docs:
        return json.dumps({"error": "no matches found"})
    chunks = [
        {
            "n": i + 1,
            "source": (metas[i] or {}).get("source", "unknown"),
            "text": docs[i],
        }
        for i in range(len(docs))
    ]

    global _provider
    if _provider is None:
        try:
            _provider = _provider_from_env()
        except Exception as e:
            return json.dumps({"error": str(e)})

    try:
        reply = _provider.complete(
            system=_SYSTEM_PROMPT,
            user=_build_user_prompt(question, chunks),
            max_tokens=max_tokens,
        )
    except Exception as e:
        log.exception("LLM provider failed")
        return json.dumps({"error": f"llm provider failed: {e}"})

    sources = [
        {"n": c["n"], "source": c["source"], "snippet": c["text"][:240]}
        for c in chunks
    ]
    model_name = getattr(_provider, "deployment", _provider.__class__.__name__)
    return json.dumps(
        {
            "answer": reply.strip(),
            "sources": sources,
            "model": model_name,
            "chunks_used": len(chunks),
        }
    )

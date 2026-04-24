# @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: BYO-embedder seam (default/openai/ollama) | prev: NEW
"""Pluggable embedding backends.

Lenders, hospitals, and any team handling regulated data refuse to ship their
content to a public-cloud embedding API. This module defines a tiny `Embedder`
Protocol plus three reference implementations:

  * ``default`` — uses ChromaDB's bundled all-MiniLM-L6-v2 (fully offline).
  * ``openai`` — OpenAI / Azure-OpenAI compatible endpoint.
  * ``ollama`` — local Ollama server (offline; recommended for on-prem).

Operators select an implementation via env vars (see ``Config``). The store
constructor accepts the resulting Embedder; tools never touch this module.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

log = logging.getLogger("recall.embedder")


@runtime_checkable
class Embedder(Protocol):
    """Convert texts into vectors. Stateless from the caller's view."""

    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class DefaultChromaEmbedder:
    """Sentinel — tells the store to use ChromaDB's built-in embedding fn.

    No model download, no API call from Recall code; Chroma handles it via
    its ``DefaultEmbeddingFunction`` (all-MiniLM-L6-v2, ONNX, ~80 MB).
    Best choice for laptops and air-gapped installs that don't have Ollama.
    """

    name = "default"

    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        # Never invoked: store passes None to Chroma which uses its default.
        raise NotImplementedError("DefaultChromaEmbedder is a sentinel")


class OpenAIEmbedder:
    """OpenAI / Azure-OpenAI / OpenAI-compatible embedder.

    Works against any endpoint that speaks the OpenAI embeddings API
    (OpenAI proper, Azure OpenAI, vLLM with --served-model-name, etc).
    """

    name = "openai"

    def __init__(self, model: str, api_key: str, base_url: str | None = None) -> None:
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError("RECALL_EMBEDDER=openai requires `pip install openai`") from e
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model
        log.info("OpenAIEmbedder ready. model=%s base_url=%s", model, base_url or "default")

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


class OllamaEmbedder:
    """Local Ollama server embedder.

    Recommended for on-prem deployments. Runs entirely inside the customer's
    network. Default endpoint matches Ollama's out-of-box config.
    """

    name = "ollama"

    def __init__(self, model: str, endpoint: str = "http://localhost:11434") -> None:
        try:
            import httpx  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError("RECALL_EMBEDDER=ollama requires `pip install httpx`") from e
        self._httpx = httpx
        self._model = model
        self._endpoint = endpoint.rstrip("/")
        log.info("OllamaEmbedder ready. model=%s endpoint=%s", model, self._endpoint)

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        with self._httpx.Client(timeout=60.0) as client:
            for t in texts:
                r = client.post(
                    f"{self._endpoint}/api/embeddings",
                    json={"model": self._model, "prompt": t},
                )
                r.raise_for_status()
                out.append(r.json()["embedding"])
        return out


def make_embedder_from_env() -> Embedder:
    """Build an Embedder per env vars. Falls back to DefaultChromaEmbedder."""
    kind = os.environ.get("RECALL_EMBEDDER", "default").lower()
    if kind == "default":
        return DefaultChromaEmbedder()
    if kind == "openai":
        return OpenAIEmbedder(
            model=os.environ.get("RECALL_EMBED_MODEL", "text-embedding-3-small"),
            api_key=os.environ.get("RECALL_EMBED_API_KEY") or os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("RECALL_EMBED_BASE_URL") or None,
        )
    if kind == "ollama":
        return OllamaEmbedder(
            model=os.environ.get("RECALL_EMBED_MODEL", "nomic-embed-text"),
            endpoint=os.environ.get("RECALL_EMBED_ENDPOINT", "http://localhost:11434"),
        )
    raise RuntimeError(f"Unknown RECALL_EMBEDDER='{kind}'. Use one of: default, openai, ollama.")

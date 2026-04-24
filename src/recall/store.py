# @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: ChromaStore accepts pluggable Embedder | prev: copilot-c4a1@2026-04-23
"""Vector store interface + ChromaDB implementation.

The Store interface is intentionally minimal — count, upsert, query, get,
delete — so alternative backends (Qdrant, Pinecone, in-memory for tests)
can be plugged in later without touching tool modules.

The Chroma implementation accepts an optional ``Embedder`` so customers can
plug in OpenAI, Azure-OpenAI, Ollama, or any other embedding backend without
shipping content to a public-cloud default.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from .embedder import DefaultChromaEmbedder, Embedder

log = logging.getLogger("recall.store")


class Store(Protocol):
    """Minimal vector store surface used by Recall tools."""

    def count(self) -> int: ...
    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None: ...
    def query(self, query_texts: list[str], n_results: int, where: dict | None = None) -> dict: ...
    def get(self, where: dict | None = None, limit: int = 100, include: list[str] | None = None) -> dict: ...
    def delete(self, ids: list[str]) -> None: ...


def _wrap_embedder_for_chroma(embedder: Embedder) -> Any:
    """Adapt a Recall ``Embedder`` to Chroma's ``EmbeddingFunction`` shape."""
    from chromadb.api.types import Documents, EmbeddingFunction, Embeddings  # type: ignore

    class _Wrapped(EmbeddingFunction):
        def __call__(self, input: Documents) -> Embeddings:  # noqa: A002 (chroma name)
            return embedder.embed(list(input))

    return _Wrapped()


class ChromaStore:
    """ChromaDB-backed implementation of Store."""

    def __init__(
        self, path: str, collection_name: str,
        embedder: Embedder | None = None,
    ) -> None:
        # Lazy import: chromadb pulls in onnxruntime + embedding model (slow cold start).
        import chromadb

        os.makedirs(path, exist_ok=True)
        log.info("Initializing ChromaDB at %s", path)
        self._client = chromadb.PersistentClient(path=path)

        # If embedder is None or DefaultChromaEmbedder, let Chroma use its
        # bundled all-MiniLM-L6-v2. Otherwise wrap and pass through.
        kwargs: dict[str, Any] = {
            "name": collection_name,
            "metadata": {"hnsw:space": "cosine"},
        }
        if embedder is not None and not isinstance(embedder, DefaultChromaEmbedder):
            kwargs["embedding_function"] = _wrap_embedder_for_chroma(embedder)
            log.info("ChromaStore using BYO embedder: %s", embedder.name)
        else:
            log.info("ChromaStore using bundled default embedder (all-MiniLM-L6-v2)")

        self._collection = self._client.get_or_create_collection(**kwargs)
        log.info(
            "ChromaDB ready. Collection '%s' has %d chunks.",
            collection_name,
            self._collection.count(),
        )

    def count(self) -> int:
        return self._collection.count()

    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_texts: list[str], n_results: int, where: dict | None = None) -> dict:
        kwargs: dict[str, Any] = {"query_texts": query_texts, "n_results": n_results}
        if where:
            kwargs["where"] = where
        return self._collection.query(**kwargs)

    def get(self, where: dict | None = None, limit: int = 100, include: list[str] | None = None) -> dict:
        kwargs: dict[str, Any] = {"limit": limit}
        if where:
            kwargs["where"] = where
        if include is not None:
            kwargs["include"] = include
        return self._collection.get(**kwargs)

    def delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)


# Module-level lazy singleton. app.py calls init_store(); tools call get_store().
_store: Store | None = None


def init_store(
    path: str, collection_name: str, embedder: Embedder | None = None,
) -> Store:
    global _store
    _store = ChromaStore(path=path, collection_name=collection_name, embedder=embedder)
    return _store


def get_store() -> Store:
    if _store is None:
        raise RuntimeError("Store not initialized — call init_store() first")
    return _store


def is_ready() -> bool:
    return _store is not None

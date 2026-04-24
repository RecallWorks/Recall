# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | checkpoint + pulse | prev: NEW
"""checkpoint — snapshot working state. pulse — read it back."""
from __future__ import annotations

import hashlib
from datetime import datetime

from ..artifacts import persist_artifact
from ..auth import BadSession, require_hex
from ..config import Config
from ..snapshot import maybe_auto_snapshot
from ..state import S
from ..store import get_store

_cfg: Config | None = None


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config


def _config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def checkpoint(
    intent: str, established: str, pursuing: str, open_questions: str,
    session: str = "", domain: str = "",
) -> str:
    """Snapshot current working state into the brain.

    Args:
        intent: Current goal (one sentence).
        established: Key facts/decisions locked in.
        pursuing: What you're actively doing next.
        open_questions: Things uncertain or needing verification.
        session: 4-hex agent id (required).
        domain: Domain tag for filtering.
    """
    cfg = _config()
    store = get_store()
    try:
        require_hex(session, "session")
    except BadSession as e:
        return str(e)
    ts = datetime.now().isoformat()
    document = (
        f"CHECKPOINT @ {ts}\nINTENT: {intent}\nESTABLISHED: {established}\n"
        f"PURSUING: {pursuing}\nOPEN QUESTIONS: {open_questions}"
    )
    chunk_id = hashlib.sha256(f"checkpoint:{ts}".encode()).hexdigest()[:16]
    metadata = {
        "source": f"checkpoint/{session}", "chunk_index": 0,
        "indexed_at": ts, "type": "checkpoint",
        "domain": domain or "general", "session": session,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(cfg.artifacts_dir, "checkpoints", f"{session}_{chunk_id}", f"# Checkpoint: {session}\n\n{document}")
    entry = {"id": chunk_id, "ts": ts, "document": document, "metadata": metadata}
    S.checkpoint_ring.append(entry)
    if len(S.checkpoint_ring) > cfg.checkpoint_ring_max:
        S.checkpoint_ring.pop(0)
    S.last_checkpoint_ts = datetime.fromisoformat(ts)
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return (
        f"Checkpoint stored @ {ts}. ID: {chunk_id}. "
        f"Ring buffer: {len(S.checkpoint_ring)}/{cfg.checkpoint_ring_max}."
    )


def pulse(domain: str = "", include_reasoning: bool = True) -> str:
    """Read back current context — checkpoint, reasoning, anti-patterns, last reflection.

    Args:
        domain: Optional domain filter for reasoning/anti-pattern lookup.
        include_reasoning: Include reasoning artifacts (default True).
    """
    store = get_store()
    sections = [_pulse_checkpoint(store)]
    if include_reasoning and store.count() > 0:
        query = domain if domain else "current work reasoning"
        for fetcher in (_pulse_reasoning, _pulse_anti_patterns):
            section = fetcher(store, query)
            if section:
                sections.append(section)
        reflection = _pulse_reflection(store)
        if reflection:
            sections.append(reflection)
    return "\n".join(sections) if sections else "No context available. Start with checkpoint()."


def _pulse_checkpoint(store) -> str:
    if S.checkpoint_ring:
        latest = S.checkpoint_ring[-1]
        return f"=== LATEST CHECKPOINT ({latest['ts']}) ===\n{latest['document']}\n"
    if store.count() > 0:
        cp = store.query(
            query_texts=["checkpoint current state intent"],
            n_results=1, where={"type": "checkpoint"},
        )
        if cp["documents"] and cp["documents"][0]:
            return f"=== LAST CHECKPOINT (from vector store) ===\n{cp['documents'][0][0]}\n"
    return "=== NO CHECKPOINT FOUND ===\nNo prior checkpoint exists.\n"


def _pulse_reasoning(store, query: str) -> str:
    r = store.query(query_texts=[query], n_results=3, where={"type": "reasoning"})
    if not (r["documents"] and r["documents"][0]):
        return ""
    lines = ["=== RELEVANT REASONING ==="]
    for doc, meta in zip(r["documents"][0], r["metadatas"][0]):
        lines.append(
            f"--- [{meta.get('domain', '?')}] confidence={meta.get('confidence', '?')} ---\n{doc}\n"
        )
    return "\n".join(lines)


def _pulse_anti_patterns(store, query: str) -> str:
    a = store.query(query_texts=[query], n_results=2, where={"type": "anti_pattern"})
    if not (a["documents"] and a["documents"][0]):
        return ""
    lines = ["=== WATCH OUT (anti-patterns) ==="]
    for doc, meta in zip(a["documents"][0], a["metadatas"][0]):
        lines.append(f"--- [{meta.get('domain', '?')}] ---\n{doc}\n")
    return "\n".join(lines)


def _pulse_reflection(store) -> str:
    r = store.query(
        query_texts=["session reflection close"],
        n_results=1, where={"type": "reflection"},
    )
    if r["documents"] and r["documents"][0]:
        return f"=== LAST SESSION REFLECTION ===\n{r['documents'][0][0]}\n"
    return ""

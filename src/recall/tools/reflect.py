# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | reflect / anti_pattern / session_close | prev: NEW
"""Structured-reasoning tools: reflect, anti_pattern, session_close.

All three require a hex agent-id session for traceability.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from ..artifacts import persist_artifact
from ..auth import BadSession, require_hex
from ..config import Config
from ..snapshot import maybe_auto_snapshot
from ..state import staleness_check
from ..store import get_store
from ..summarizer import NoopSummarizer, get_summarizer

_cfg: Config | None = None


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config


def _config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def reflect(
    domain: str,
    hypothesis: str,
    reasoning: str,
    result: str,
    revised_belief: str,
    next_time: str,
    confidence: float = 0.7,
    session: str = "",
) -> str:
    """Store a structured reasoning artifact.

    Args:
        domain: Area this applies to.
        hypothesis: What you believed or tried.
        reasoning: Why you tried it.
        result: What happened (start with SUCCESS, FAILED, or PARTIAL).
        revised_belief: What you now believe.
        next_time: Concrete action for next agent.
        confidence: Confidence in revised belief (0.0-1.0).
        session: 4-hex agent id (required).
    """
    cfg = _config()
    store = get_store()
    try:
        require_hex(session, "session")
    except BadSession as e:
        return str(e)
    confidence = max(0.0, min(1.0, confidence))
    document = (
        f"DOMAIN: {domain}\nHYPOTHESIS: {hypothesis}\nREASONING: {reasoning}\n"
        f"RESULT: {result}\nREVISED BELIEF: {revised_belief}\n"
        f"NEXT TIME: {next_time}\nCONFIDENCE: {confidence}"
    )
    chunk_id = hashlib.sha256(
        f"reasoning:{domain}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]
    metadata = {
        "source": f"reasoning/{domain}",
        "chunk_index": 0,
        "indexed_at": datetime.now().isoformat(),
        "type": "reasoning",
        "domain": domain,
        "result": result.split()[0] if result else "UNKNOWN",
        "confidence": confidence,
        "session": session,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "reasoning",
        f"{domain}_{chunk_id}",
        f"# Reasoning: {domain}\n\n{document}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return (
        f"Reasoning stored. Domain: {domain}, Result: {metadata['result']}, "
        f"Confidence: {confidence}, ID: {chunk_id}"
    ) + staleness_check(cfg.stale_minutes)


def anti_pattern(
    domain: str,
    temptation: str,
    why_wrong: str,
    signature: str,
    instead: str,
    session: str = "",
) -> str:
    """Store a temptation signature -- a pattern that LOOKS right but isn't.

    Args:
        domain: Area this applies to.
        temptation: What looks appealing.
        why_wrong: Why it's actually harmful.
        signature: The feeling/impulse to recognize.
        instead: What to do instead.
        session: 4-hex agent id (required).
    """
    cfg = _config()
    store = get_store()
    try:
        require_hex(session, "session")
    except BadSession as e:
        return str(e)
    document = (
        f"DOMAIN: {domain}\nTEMPTATION: {temptation}\nWHY WRONG: {why_wrong}\n"
        f"SIGNATURE: {signature}\nINSTEAD: {instead}"
    )
    chunk_id = hashlib.sha256(
        f"anti_pattern:{domain}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]
    metadata = {
        "source": f"anti-pattern/{domain}",
        "chunk_index": 0,
        "indexed_at": datetime.now().isoformat(),
        "type": "anti_pattern",
        "domain": domain,
        "session": session,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "anti_patterns",
        f"{domain}_{chunk_id}",
        f"# Anti-Pattern: {domain}\n\n{document}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return f"Anti-pattern stored. Domain: {domain}, ID: {chunk_id}" + staleness_check(
        cfg.stale_minutes
    )


def session_close(
    session_id: str,
    reasoning_changed: str,
    do_differently: str,
    still_uncertain: str,
    temptations: str,
) -> str:
    """End-of-session reflection.

    Args:
        session_id: 4-hex agent id (required).
        reasoning_changed: What beliefs changed this session.
        do_differently: Shortcuts for next time.
        still_uncertain: Open hypotheses.
        temptations: Obvious-looking wrong moves to avoid.
    """
    cfg = _config()
    store = get_store()
    try:
        require_hex(session_id, "session_id")
    except BadSession as e:
        return str(e)
    raw_document = (
        f"SESSION: {session_id}\nREASONING CHANGED: {reasoning_changed}\n"
        f"DO DIFFERENTLY: {do_differently}\nSTILL UNCERTAIN: {still_uncertain}\n"
        f"TEMPTATIONS: {temptations}"
    )
    # If a real summarizer is configured (not noop), condense the narrative
    # into a tighter retrieval chunk. Raw fields stay in the artifact.
    summarizer = get_summarizer()
    if isinstance(summarizer, NoopSummarizer):
        document = raw_document
        summarizer_used = "noop"
    else:
        try:
            condensed = summarizer.summarize(raw_document, max_words=180)
            document = f"SESSION: {session_id}\nSUMMARY ({summarizer.name}): {condensed}"
            summarizer_used = summarizer.name
        except Exception:
            # Fall back to raw on any LLM error — never lose a reflection.
            document = raw_document
            summarizer_used = "noop-fallback"

    chunk_id = hashlib.sha256(
        f"reflection:{session_id}:{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]
    metadata = {
        "source": f"reflection/{session_id}",
        "chunk_index": 0,
        "indexed_at": datetime.now().isoformat(),
        "type": "reflection",
        "domain": "session",
        "session": session_id,
        "summarizer": summarizer_used,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "reflections",
        f"{session_id}_{chunk_id}",
        f"# Session Reflection: {session_id}\n\n{raw_document}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return (
        f"Session reflection stored for {session_id}. ID: {chunk_id}. "
        f"Summarizer: {summarizer_used}."
    ) + staleness_check(cfg.stale_minutes)

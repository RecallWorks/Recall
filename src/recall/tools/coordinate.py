# @wbx-modified copilot-a3f7 | 2026-04-30 00:55 MTN | v0.1 | multi-agent coordination primitives (claim/release/handoff/who_has/pulse_others) | prev: NEW
"""Multi-agent coordination — the wedge that separates Recall from
single-agent memory tools.

Most memory servers (mem0, Letta, Zep) optimize for one agent across
many sessions. Recall adds primitives for many agents in one session:

  * claim(resource, agent, ttl)  — soft lock with auto-expiring TTL
  * release(resource, agent)     — explicit unlock (soft-archive per guardrail)
  * who_has(resource)            — current claimer or None if expired/unclaimed
  * claims()                     — list all active (non-expired) claims
  * handoff(to_agent, ...)       — explicit work transfer w/ context
  * pulse_others(self_agent)     — see what OTHER agents are doing right now

These are MCP tools with their own metadata.type values. They piggyback on
the existing Chroma store and artifact persistence — no new dependencies.

Design notes:
  * Claims are advisory (soft locks). Recall does not enforce — clients do.
    This matches how git locks work; nothing physically prevents a second
    agent from editing, but every well-behaved client checks first.
  * TTLs prevent stale locks from a crashed agent freezing a resource forever.
  * Releases are archived, not deleted, per the project-wide delete=archive
    guardrail. Audit trail of who locked what when survives.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime

from ..artifacts import persist_artifact
from ..auth import BadSession, require_hex
from ..config import Config
from ..snapshot import maybe_auto_snapshot
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


def _now_epoch() -> float:
    return time.time()


def _resource_id(resource: str) -> str:
    """Stable id for a resource string (e.g. file path, table name, URL)."""
    return hashlib.sha256(resource.encode("utf-8")).hexdigest()[:16]


# ---------- claim --------------------------------------------------------

def claim(
    resource: str,
    agent: str,
    ttl_seconds: int = 600,
    note: str = "",
) -> str:
    """Soft-lock a resource for the calling agent.

    Returns a JSON string with status. Status values:
      * "claimed"  — lock acquired (was free or self-renewal)
      * "blocked"  — another agent currently holds the claim; includes their
                     agent id, ttl_remaining_seconds, and original note

    Args:
        resource: Free-form resource identifier (file path, URL, table name).
        agent: 4-hex agent id of the caller.
        ttl_seconds: Lock lifetime. Default 600 (10 min). Max 86400 (1 day).
        note: Optional human-readable purpose ("refactoring auth module").
    """
    try:
        require_hex(agent, "agent")
    except BadSession as e:
        return json.dumps({"status": "error", "error": str(e)})

    if ttl_seconds < 1 or ttl_seconds > 86400:
        return json.dumps({"status": "error", "error": "ttl_seconds must be 1..86400"})

    cfg = _config()
    store = get_store()
    rid = _resource_id(resource)
    now = _now_epoch()
    expires = now + ttl_seconds
    ts = datetime.now().isoformat()

    # Look up existing active claim
    existing = _active_claim(store, rid)
    if existing is not None and existing["agent"] != agent:
        return json.dumps({
            "status": "blocked",
            "resource": resource,
            "held_by": existing["agent"],
            "ttl_remaining_seconds": int(existing["expires_epoch"] - now),
            "note": existing.get("note", ""),
            "claimed_at": existing.get("ts", ""),
        })

    # Acquire (new or self-renewal). Use a stable id so re-claim by same
    # agent overwrites cleanly.
    chunk_id = f"claim_{rid}_{agent}"
    document = (
        f"CLAIM @ {ts}\nRESOURCE: {resource}\nAGENT: {agent}\n"
        f"TTL: {ttl_seconds}s\nEXPIRES: {datetime.fromtimestamp(expires).isoformat()}\n"
        f"NOTE: {note}"
    )
    metadata = {
        "source": f"claim/{agent}",
        "chunk_index": 0,
        "indexed_at": ts,
        "indexed_at_epoch": now,
        "type": "claim",
        "resource": resource,
        "resource_id": rid,
        "agent": agent,
        "ttl_seconds": ttl_seconds,
        "expires_epoch": expires,
        "note": note,
        "archived": False,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "claims",
        f"{rid}_{agent}_{int(now)}",
        f"# Claim: {resource}\n\n{document}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return json.dumps({
        "status": "claimed",
        "resource": resource,
        "agent": agent,
        "ttl_seconds": ttl_seconds,
        "expires_at": datetime.fromtimestamp(expires).isoformat(),
    })


# ---------- release ------------------------------------------------------

def release(resource: str, agent: str) -> str:
    """Explicitly release a claim. Soft-archive, not delete.

    Returns JSON with status:
      * "released" — claim found and archived
      * "not_held" — agent does not currently hold a claim on this resource
    """
    try:
        require_hex(agent, "agent")
    except BadSession as e:
        return json.dumps({"status": "error", "error": str(e)})

    store = get_store()
    rid = _resource_id(resource)
    chunk_id = f"claim_{rid}_{agent}"

    # Soft-archive: flip metadata.archived = True so active queries skip it.
    # Per delete=archive guardrail, no physical removal.
    try:
        existing = store.get_by_ids(ids=[chunk_id])
    except Exception:
        existing = {"ids": [], "metadatas": []}

    if not existing.get("ids"):
        return json.dumps({"status": "not_held", "resource": resource, "agent": agent})

    md = (existing.get("metadatas") or [{}])[0] or {}
    md["archived"] = True
    md["archived_at"] = datetime.now().isoformat()
    store.update_metadatas(ids=[chunk_id], metadatas=[md])
    return json.dumps({
        "status": "released",
        "resource": resource,
        "agent": agent,
    })


# ---------- who_has ------------------------------------------------------

def who_has(resource: str) -> str:
    """Return current claimer of a resource, or null if free/expired.

    Returns JSON: {"resource", "held_by"|null, "ttl_remaining_seconds", "note", "claimed_at"}
    """
    store = get_store()
    rid = _resource_id(resource)
    claim_rec = _active_claim(store, rid)
    if claim_rec is None:
        return json.dumps({"resource": resource, "held_by": None})
    return json.dumps({
        "resource": resource,
        "held_by": claim_rec["agent"],
        "ttl_remaining_seconds": int(claim_rec["expires_epoch"] - _now_epoch()),
        "note": claim_rec.get("note", ""),
        "claimed_at": claim_rec.get("ts", ""),
    })


# ---------- claims (list) ------------------------------------------------

def claims() -> str:
    """List all active (non-expired, non-archived) claims across all agents.

    Returns JSON: {"count": N, "claims": [{"resource", "held_by",
    "ttl_remaining_seconds", "note", "claimed_at"}, ...]}.
    """
    store = get_store()
    now = _now_epoch()
    try:
        result = store.get(where={"type": "claim"})
    except Exception:
        return json.dumps({"count": 0, "claims": []})

    out: list[dict] = []
    for md in result.get("metadatas") or []:
        if not md or md.get("archived"):
            continue
        if md.get("expires_epoch", 0) <= now:
            continue
        out.append({
            "resource": md.get("resource", ""),
            "held_by": md.get("agent", ""),
            "ttl_remaining_seconds": int(md.get("expires_epoch", 0) - now),
            "note": md.get("note", ""),
            "claimed_at": md.get("indexed_at", ""),
        })
    out.sort(key=lambda r: -r["ttl_remaining_seconds"])
    return json.dumps({"count": len(out), "claims": out})


# ---------- handoff ------------------------------------------------------

def handoff(
    to_agent: str,
    from_agent: str,
    intent: str,
    files: str = "",
    context: str = "",
) -> str:
    """Explicit work-transfer artifact.

    Use when one agent is leaving a task in a state another agent needs to
    pick up. The receiving agent reads handoffs via pulse_others() or
    recall_filtered(type='handoff').

    Args:
        to_agent: 4-hex id of receiving agent.
        from_agent: 4-hex id of sending agent.
        intent: One sentence: what the receiver should do next.
        files: Optional comma-separated file paths to focus on.
        context: Free-form context — what was done, what's still pending.
    """
    try:
        require_hex(from_agent, "from_agent")
        require_hex(to_agent, "to_agent")
    except BadSession as e:
        return json.dumps({"status": "error", "error": str(e)})

    cfg = _config()
    store = get_store()
    ts = datetime.now().isoformat()
    now = _now_epoch()
    chunk_id = hashlib.sha256(f"handoff:{from_agent}:{to_agent}:{ts}".encode()).hexdigest()[:16]
    document = (
        f"HANDOFF @ {ts}\nFROM: {from_agent}\nTO: {to_agent}\n"
        f"INTENT: {intent}\nFILES: {files}\nCONTEXT: {context}"
    )
    metadata = {
        "source": f"handoff/{from_agent}->{to_agent}",
        "chunk_index": 0,
        "indexed_at": ts,
        "indexed_at_epoch": now,
        "type": "handoff",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "intent": intent,
        "files": files,
    }
    store.upsert(ids=[chunk_id], documents=[document], metadatas=[metadata])
    persist_artifact(
        cfg.artifacts_dir,
        "handoffs",
        f"{from_agent}_to_{to_agent}_{chunk_id}",
        f"# Handoff: {from_agent} -> {to_agent}\n\n{document}",
    )
    maybe_auto_snapshot(cfg.store_dir, cfg.prebuilt_dir, cfg.auto_snapshot_every)
    return json.dumps({
        "status": "delivered",
        "id": chunk_id,
        "ts": ts,
        "from": from_agent,
        "to": to_agent,
    })


# ---------- pulse_others -------------------------------------------------

def pulse_others(self_agent: str, n: int = 5, domain: str = "") -> str:
    """Show what OTHER agents have been doing recently.

    Returns the most recent N checkpoints from agents OTHER than self_agent.
    The single most useful coordination call: before starting work, see who
    else is active and on what.

    Args:
        self_agent: 4-hex id of caller (results EXCLUDE this agent).
        n: Max checkpoints to return (default 5, capped 20).
        domain: Optional domain filter (e.g. 'auth-refactor').
    """
    try:
        require_hex(self_agent, "self_agent")
    except BadSession as e:
        return json.dumps({"status": "error", "error": str(e)})
    n = max(1, min(20, n))
    store = get_store()
    try:
        where: dict = {"type": "checkpoint"}
        # NOTE: chromadb where-clauses don't easily express "session != X";
        # over-fetch then filter in Python. Cheap at agent-count scale (<50).
        result = store.get(where=where, limit=200)
    except Exception:
        return json.dumps({"count": 0, "checkpoints": []})

    rows: list[dict] = []
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []
    for doc, md in zip(docs, metas, strict=False):
        if not md:
            continue
        if md.get("session") == self_agent:
            continue
        if domain and md.get("domain", "") != domain:
            continue
        rows.append({
            "agent": md.get("session", ""),
            "domain": md.get("domain", ""),
            "ts": md.get("indexed_at", ""),
            "ts_epoch": md.get("indexed_at_epoch", 0) or 0,
            "document": doc,
        })
    rows.sort(key=lambda r: -r["ts_epoch"])
    rows = rows[:n]
    # Drop ts_epoch from output (used only for sort).
    for r in rows:
        r.pop("ts_epoch", None)
    return json.dumps({"count": len(rows), "checkpoints": rows})


# ---------- internals ----------------------------------------------------

def _active_claim(store, resource_id: str) -> dict | None:
    """Return the active (non-archived, non-expired) claim metadata for a
    resource, or None if free.
    """
    now = _now_epoch()
    try:
        result = store.get(where={"resource_id": resource_id})
    except Exception:
        return None
    metas = result.get("metadatas") or []
    best: dict | None = None
    for md in metas:
        if not md or md.get("type") != "claim":
            continue
        if md.get("archived"):
            continue
        exp = md.get("expires_epoch", 0)
        if exp <= now:
            continue
        # Latest non-expired wins (latest indexed_at_epoch).
        if best is None or (md.get("indexed_at_epoch", 0) > best.get("indexed_at_epoch", 0)):
            best = {
                "agent": md.get("agent", ""),
                "expires_epoch": exp,
                "ts": md.get("indexed_at", ""),
                "note": md.get("note", ""),
                "indexed_at_epoch": md.get("indexed_at_epoch", 0),
            }
    return best

# @wbx-modified copilot-b1c4 | 2026-04-27 21:42 MTN | v1.2 | refined family heuristic + single-family trigger + compute_confidence opt-in (a3f7 align) | prev: copilot-b1c4@2026-04-27 21:14 MTN
"""recall_filtered — structural query over indexed metadata.

Lets agents ask questions semantic search can't:
  - "all anti_patterns from copilot-a3f7 in last 7 days"
  - "checkpoints where domain=icewhisperer-gateway"

Filters BEFORE semantic match. Returns the SAME envelope shape as recall:
  {result, results}. HTTP layer wraps with {tool, by}.

v1.2 additive opts (no breaking change):
  - diversity=False (default OFF — opt-in via gateway).
  - compute_confidence=False (default OFF — opt-in via gateway).
    When ON, envelope adds {low_confidence, families} so gateway can
    skip its own pass (brain wins as single source of truth).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..config import Config
from ..state import staleness_check
from ..store import get_store
from .recall import _format_recall_string

_VALID_TYPES = {
    "all",
    "reasoning",
    "anti_pattern",
    "reflection",
    "observation",
    "document",
    "checkpoint",
}


def _parse_since(since: str) -> tuple[float | None, str | None]:
    """Parse since= into (epoch_threshold, iso_threshold).

    Returns (None, None) for empty/unparseable.
    Accepts: '7d', '24h', '30m', or an ISO datetime string.
    """
    if not since:
        return None, None
    s = since.strip().lower()
    if len(s) >= 2 and s[-1] in ("d", "h", "m") and s[:-1].isdigit():
        n = int(s[:-1])
        unit = s[-1]
        delta = {"d": timedelta(days=n), "h": timedelta(hours=n), "m": timedelta(minutes=n)}[unit]
        threshold_dt = datetime.now() - delta
        return threshold_dt.timestamp(), threshold_dt.isoformat()
    try:
        dt = datetime.fromisoformat(since)
        return dt.timestamp(), dt.isoformat()
    except (ValueError, TypeError):
        return None, None


def _build_filter(
    type: str,
    domain: str,
    session: str,
    source_prefix: str,
    since_epoch: float | None = None,
    since_iso: str | None = None,
) -> dict | None:
    """Build a ChromaDB where-filter from structured params. None = no filter.

    For time windows: epoch-only ($gte numeric). Chunks indexed before the
    dual-write landed lack indexed_at_epoch and won't match a since= window
    until backfill_epoch runs — that's the correct semantic (ChromaDB
    rejects $gte on string fields).
    """
    clauses: list[dict] = []
    if type and type != "all":
        clauses.append({"type": type})
    if domain:
        clauses.append({"domain": domain})
    if session:
        bare = session.replace("copilot-", "")
        clauses.append({"$or": [{"session": bare}, {"session": f"copilot-{bare}"}]})
    # source_prefix handled post-query (no native prefix op in ChromaDB).
    if since_epoch is not None:
        clauses.append({"indexed_at_epoch": {"$gte": since_epoch}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _source_family(source: str) -> str:
    """Family key — finer cut than first path component.

    Heuristic (matches a3f7 gateway-side):
      1. If filename has 4+ dotted segments (SDK doc spam like
         'EllieMae.Encompass.Configuration.CustomField.md'), use the
         first 4 dotted segments as the family — collapses one type
         per namespace branch.
      2. Otherwise, use the parent directory of the file.
      3. Fallback to the source itself if no path separator.
    """
    if not source:
        return ""
    src = source.replace("\\", "/").strip("/")
    if not src:
        return ""
    parts = src.split("/")
    leaf = parts[-1]
    # Strip extension for dotted-segment counting
    stem = leaf.rsplit(".", 1)[0] if "." in leaf else leaf
    dotted = stem.split(".")
    if len(dotted) >= 4:
        return ".".join(dotted[:4])
    if len(parts) >= 2:
        return parts[-2]
    return parts[0]


def _diversify(rows: list[dict], n: int, min_families: int) -> list[dict]:
    """Reorder rows so top-n covers as many distinct source families as
    possible. Stable within family (preserves rank order). Returns the
    full list with rebalanced top, capped at len(rows).
    """
    if not rows or n <= 1:
        return rows
    families: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in rows:
        fam = _source_family(r.get("source", "") or "")
        if fam not in families:
            families[fam] = []
            order.append(fam)
        families[fam].append(r)
    if len(order) < min_families:
        return rows  # not enough diversity available; leave as-is
    # Round-robin until we have n picks (or exhaust all).
    picked: list[dict] = []
    while len(picked) < n and any(families[f] for f in order):
        for fam in order:
            if not families[fam]:
                continue
            picked.append(families[fam].pop(0))
            if len(picked) >= n:
                break
    # Tail = remaining rows preserving their original relative order.
    leftover = [r for fam in order for r in families[fam]]
    out = picked + leftover
    for i, r in enumerate(out):
        r["rank"] = i + 1
    return out


def _low_confidence(rows: list[dict], spread: float = 0.05, floor: float = 0.30) -> bool:
    """Flag weak-retrieval signal. Two triggers (matches a3f7):

      A. Single-family clustering: n>=4 AND all rows from same family.
         Most common failure mode in the IW corpus (SDK-reference spam).
      B. Tight + high distance: n>=3, max-min spread<=spread, mean>floor.
    """
    if not rows:
        return False
    # Trigger A — single family with n>=4
    if len(rows) >= 4:
        families = {_source_family(r.get("source", "") or "") for r in rows}
        families.discard("")
        if len(families) == 1:
            return True
    # Trigger B — tight cluster + high mean distance
    dists = [r["distance"] for r in rows if r.get("distance") is not None]
    if len(dists) < 3:
        return False
    if (max(dists) - min(dists)) > spread:
        return False
    return (sum(dists) / len(dists)) > floor


def _recall_filtered_structured(
    query: str = "",
    n: int = 20,
    type: str = "all",
    domain: str = "",
    session: str = "",
    source_prefix: str = "",
    since: str = "",
    diversity: bool = False,
    min_diversity: int = 2,
    compute_confidence: bool = False,
    config: Config | None = None,
) -> dict:
    """Structured-array variant. Same envelope as recall: {result, results}."""
    cfg = config or _default_config()
    if type not in _VALID_TYPES:
        msg = f"Invalid type '{type}'. Must be one of: {', '.join(sorted(_VALID_TYPES))}"
        return {"result": msg, "results": [], "error": msg}
    n = min(max(n, 1), 100)
    store = get_store()
    if store.count() == 0:
        return {"result": "Memory is empty. Run 'reindex' first.", "results": []}
    since_epoch, since_iso = _parse_since(since) if since else (None, None)
    if since and since_epoch is None:
        msg = f"Invalid since='{since}'. Use '7d'/'24h'/'30m' or ISO datetime."
        return {"result": msg, "results": [], "error": msg}
    where = _build_filter(
        type, domain, session, source_prefix,
        since_epoch=since_epoch, since_iso=since_iso,
    )

    # Over-fetch when diversifying so we have raw material to rebalance.
    fetch_n = min(n * 2, 100) if diversity else n

    rows: list[dict] = []
    if query:
        res = store.query(query_texts=[query], n_results=fetch_n, where=where)
        docs = res["documents"][0] if res.get("documents") else []
        metas = res["metadatas"][0] if res.get("metadatas") else []
        dists = res["distances"][0] if res.get("distances") else [None] * len(docs)
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists, strict=False)):
            rows.append(
                {
                    "rank": i + 1,
                    "distance": float(dist) if dist is not None else None,
                    "type": meta.get("type", "document"),
                    "source": meta.get("source", "unknown"),
                    "domain": meta.get("domain", "") or None,
                    "confidence": meta.get("confidence"),
                    "text": doc,
                }
            )
    else:
        # Pure structural pull — no embedding.
        res = store.get(where=where, limit=fetch_n)
        docs = res.get("documents") or []
        metas = res.get("metadatas") or []
        for i, (doc, meta) in enumerate(zip(docs, metas, strict=False)):
            rows.append(
                {
                    "rank": i + 1,
                    "distance": None,
                    "type": meta.get("type", "document"),
                    "source": meta.get("source", "unknown"),
                    "domain": meta.get("domain", "") or None,
                    "confidence": meta.get("confidence"),
                    "text": doc,
                }
            )
    if source_prefix:
        rows = [r for r in rows if r["source"].startswith(source_prefix)]
        for i, r in enumerate(rows):
            r["rank"] = i + 1

    if diversity:
        rows = _diversify(rows, n=n, min_families=max(min_diversity, 1))

    # Trim to the caller-requested n after rerank.
    rows = rows[:n]
    for i, r in enumerate(rows):
        r["rank"] = i + 1

    body = _format_recall_string(rows)
    payload: dict = {"result": body, "results": rows}
    if compute_confidence:
        low_conf = _low_confidence(rows)
        families = sorted({_source_family(r.get("source", "") or "") for r in rows} - {""})
        payload["low_confidence"] = low_conf
        payload["families"] = families
        if low_conf:
            payload["result"] = (
                "[low-confidence: weak retrieval signal — single-family or tight high-distance cluster]\n"
                + body
            )
    payload["result"] += staleness_check(cfg.stale_minutes)
    return payload


def recall_filtered(
    query: str = "",
    n: int = 20,
    type: str = "all",
    domain: str = "",
    session: str = "",
    source_prefix: str = "",
    since: str = "",
    diversity: bool = False,
    min_diversity: int = 2,
    compute_confidence: bool = False,
    config: Config | None = None,
) -> str:
    """Structural query over brain metadata. Filters BEFORE semantic match.

    Args:
        query: Optional natural-language query. Empty = pure structural pull.
        n: Max results (default 20, hard cap 100).
        type: all|reasoning|anti_pattern|reflection|observation|document|checkpoint
        domain: Exact domain match (e.g. 'icewhisperer-gateway').
        session: Hex agent id, with or without 'copilot-' prefix.
        source_prefix: Match if metadata.source startswith this string.
        since: Time window — '7d', '24h', '30m', or ISO datetime.
        diversity: If True, over-fetch and rebalance results across distinct
            source families. Default False (back-compat / opt-in by gateway).
        min_diversity: Minimum distinct families required to trigger rerank.
        compute_confidence: If True, envelope adds {low_confidence, families}.
            Default False (back-compat / opt-in). Gateway can use this to
            skip its own pass — brain wins as single source of truth.
    """
    payload = _recall_filtered_structured(
        query=query, n=n, type=type, domain=domain, session=session,
        source_prefix=source_prefix, since=since,
        diversity=diversity, min_diversity=min_diversity,
        compute_confidence=compute_confidence, config=config,
    )
    return payload["result"]


_cfg: Config | None = None


def _default_config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def set_config(config: Config) -> None:
    global _cfg
    _cfg = config

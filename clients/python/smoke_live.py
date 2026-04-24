# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | live SDK smoke against running Recall container
"""Live smoke test against a Recall container.

Run order:
  docker run -d --name recall-smoke -p 8799:8787 -e API_KEY=smoke-key ghcr.io/recallworks/recall:0.1.0
  python smoke_live.py
"""

from __future__ import annotations

import asyncio
import sys

from recall_client import (
    AsyncRecallClient,
    RecallAuthError,
    RecallClient,
)

BASE = "http://localhost:8799"
KEY = "smoke-key"


def sync_smoke() -> None:
    print("=== sync smoke ===")
    with RecallClient(BASE, api_key=KEY) as c:
        h = c.health()
        print(f"health: {h}")
        assert h["status"] == "ok", h

        r = c.remember("the user prefers dark mode", tags="pref,ui")
        print(f"remember: {r.result[:80]}")
        assert r.tool == "remember"

        c.remember("favorite color is orange", tags="pref")
        c.remember("monitor resolution is 4K", tags="pref,ui")

        rec = c.recall("user preferences", n=3)
        print(f"recall ({len(rec.result)} chars):")
        print(rec.result[:300])
        assert rec.tool == "recall"
        assert rec.result, "recall must return non-empty markdown"

        stats = c.memory_stats()
        print(f"memory_stats: {stats.result[:160]}")

        cp = c.checkpoint(
            intent="validate SDK 0.2.0 against live server",
            established="X-API-Key auth + envelope shape match",
            pursuing="bump to 0.2.0 + republish",
            open_questions="confirm npm/pypi tokens",
            session="a3f7",
        )
        print(f"checkpoint: {cp.result[:120]}")

    print("--- sync auth-error path ---")
    bad = RecallClient(BASE, api_key="WRONG")
    try:
        bad.remember("should fail")
        raise AssertionError("expected auth error")
    except RecallAuthError as e:
        print(f"  got expected RecallAuthError: {str(e)[:60]}")
    finally:
        bad.close()


async def async_smoke() -> None:
    print("=== async smoke ===")
    async with AsyncRecallClient(BASE, api_key=KEY) as c:
        h = await c.health()
        print(f"health: {h['status']}")
        r = await c.remember("async memory works fine", tags="async")
        print(f"async remember: {r.result[:60]}")
        rec = await c.recall("async", n=2)
        print(f"async recall: {rec.result[:120]}")
        assert rec.result


def main() -> int:
    try:
        sync_smoke()
        asyncio.run(async_smoke())
    except Exception as e:
        print(f"SMOKE FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print("\nALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

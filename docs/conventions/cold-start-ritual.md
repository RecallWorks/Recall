<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: cold-start ritual | prev: copilot-c4a1@2026-04-23 -->
# Cold-Start Ritual

Every agent session that uses Recall should run the same opening protocol so
prior context is inherited deterministically.

## 1. Mint a hex agent id

A new four-character hex id (e.g. `a3f7`, `b8d2`, `c4a1`) per session. This id
is required by every write-side tool (`reflect`, `anti_pattern`, `checkpoint`,
`session_close`) so brain entries can be traced back to a specific session.

```text
session = "c4a1"
```

## 2. Pulse

Read back the latest checkpoint, recent reasoning, and active anti-patterns
in one call:

```bash
curl -X POST $RECALL_URL/tool/pulse \
  -H "X-API-Key: $RECALL_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

If pulse returns "no checkpoint", you are starting cold. That is fine — your
first checkpoint after non-trivial work will become the next session's pulse.

## 3. Targeted recall

Pull anything specific you need to inherit:

```bash
curl -X POST $RECALL_URL/tool/recall \
  -H "X-API-Key: $RECALL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"<topic of last session>","n":5}'
```

## 4. Work

While working, use the brain as a notebook:

| When                                            | Call                                |
|-------------------------------------------------|-------------------------------------|
| Discovered a fact worth keeping                 | `remember`                          |
| Tried something, learned something              | `reflect`                           |
| Caught a pattern that looks right but isn't     | `anti_pattern`                      |
| Reached a meaningful waypoint (~every 5 turns)  | `checkpoint`                        |

## 5. Close

At session end:

```bash
curl -X POST $RECALL_URL/tool/session_close \
  -H "X-API-Key: $RECALL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"c4a1",
    "reasoning_changed":"...",
    "do_differently":"...",
    "still_uncertain":"...",
    "temptations":"..."
  }'
```

`session_close` triggers the auto-snapshot (if enabled), so the next session
boots from a fresh durable copy.

## Why hex ids?

Short hex ids (4 chars = 65,536 possibilities) are:

- **Memorable enough** for an agent to keep in working context
- **Unique enough** in practice for a single team's session traffic
- **Greppable** across artifact files
- **Validation-friendly** — one regex catches malformed ids before they pollute
  the store

If you collide with a prior session id, mint another. The store doesn't enforce
uniqueness; collisions are a self-correcting cosmetic issue, not a data problem.

<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: contribution guide | prev: NEW -->
# Contributing to Recall

Thanks for your interest. Recall is a small project with strong opinions; please
read this before opening a PR.

## What we accept

- **Bug fixes** to the OSS core (`server/`, `clients/`, `docker/single-tenant/`).
- **New `Store` backends** (postgres, sqlite, lancedb, etc.) under `server/store/`.
- **Documentation improvements** — especially anti-pattern entries that capture
  a real lesson learned.
- **Examples** — MCP client configs, deployment recipes, integration patterns.
- **Test coverage** for existing code.

## What we don't accept

- Features that duplicate or compete with the `enterprise/` tree.
- Architectural rewrites without a prior issue + design discussion.
- Cosmetic refactors with no behavior change.
- Dependency bumps without a reason.

## Process

1. Open an issue first for anything beyond a typo or a clear bug fix.
2. Fork, branch, commit. Sign your commits with `git commit -s` (DCO).
3. Run `pytest` and `ruff check` locally — both must pass.
4. Open a PR against `main` with a short rationale and a test if applicable.
5. One maintainer review + green CI = merge.

## Style

- Python 3.11+. Type hints required on public APIs. `ruff` + `mypy --strict`
  on `server/` and `clients/python/`.
- Tests use `pytest` with `FakeStore` for unit tests and a real Chroma store
  for integration tests.
- No new dependencies without a clear justification in the PR description.

## DCO

We use the Developer Certificate of Origin. Sign each commit:

```
git commit -s -m "your message"
```

That adds a `Signed-off-by:` trailer asserting you have the right to submit the
contribution under the project license.

## Code of Conduct

See `CODE_OF_CONDUCT.md`. TL;DR: be kind, be specific, ship something.

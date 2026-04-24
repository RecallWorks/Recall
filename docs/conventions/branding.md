<!-- @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 5 — branding convention | prev: NEW -->
# Signed-Edit Branding

A simple, low-overhead convention for tracking which agent (and which session)
last touched a file.

## The signature

Every file an agent modifies gets a one-line header comment:

```text
@wbx-modified <agent>·<hex> | <YYYY-MM-DD> | <reason> | prev: <who>@<date>
```

Use the comment syntax appropriate to the file:

| File type            | Marker                       |
|----------------------|------------------------------|
| `.py`, `.sh`, `.ps1` | `# @wbx-modified ...`        |
| `.md`, `.html`       | `<!-- @wbx-modified ... -->` |
| `.js`, `.ts`, `.css` | `/* @wbx-modified ... */`    |

## Why

- **Traceability** — `git blame` already does this, but the inline marker
  survives format conversions, copy-paste between tools, and review threads
  where blame isn't visible.
- **Context for the next agent** — when a follow-up session opens the file,
  the header is the first thing in the buffer.
- **Cheap discipline** — one line per file, written once per session.

## Anti-patterns

- **Don't** add a new branding line on every edit within the same session.
  Update the existing one.
- **Don't** brand files you only read.
- **Don't** brand auto-generated files (`pyproject.toml` lock files,
  build artifacts).

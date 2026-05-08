<!-- @wbx-modified copilot-a3f7·MTN | 2026-05-07 | initial Recall · Agent OS public README | prev: (new) -->

# Recall™ · Agent OS

**A reference architecture for durable AI coding work.**

When AI coding agents stay long enough to do real work, they hit three walls:

1. **Statelessness** — every conversation starts cold; memory is whatever the host platform decides to keep.
2. **Cost** — autonomous loops can burn tokens or cloud spend faster than you can intervene.
3. **Audit** — what survives is the chat scrollback, until an opaque summarizer compacts it.

Agent OS is six composable pillars and a small set of conventions that turn any AI coding agent into a contractor with a project log instead of a goldfish.

> Read the whitepaper: **<https://recall.works/agent-os>**
> _(or open `site/agent-os.html` locally — same content, no internet required)_

---

## What this repo contains

```
agent-os/
├── README.md           ← you are here
├── LICENSE             ← MIT
├── config.example.json ← copy to config.json and edit
├── bootstrap.ps1       ← Windows install: dirs + scheduled tasks + templates
├── install.sh          ← cross-platform follow-up (v0.2)
├── bin/                ← reference-implementation scripts (PowerShell, no deps)
├── templates/          ← starter memory files (routing, audit-trail, REVIVAL)
├── brain/              ← networked-brain container blueprint (v0.2)
└── docs/               ← QUICKSTART + design notes
```

## Status

**v0.1 · seed.** This is the initial public skeleton. The whitepaper is finished. The reference scripts work in place (running in production at the originating workstation right now). What's published here is being de-personalized — names, paths, account IDs being replaced by config knobs — one script at a time. Each script's header tells you whether it's `READY` or still has a `TODO: de-personalize` notice.

Pull requests welcome. Issues welcome. The pattern is what matters; the code is one valid implementation.

## Get the bits

Three options, ordered by ambition:

**1. Read the whitepaper, build your own.** Everything you need is at <https://recall.works/agent-os>. The pattern is the deliverable.

**2. Copy a script, run it on your machine.** Every script in `bin/` is self-contained PowerShell with a parameter block at the top. No global state, no install ceremony.

**3. Bootstrap the whole thing.**

```powershell
# Windows / PowerShell 7+
git clone https://github.com/recall-works/agent-os
cd agent-os
cp config.example.json config.json
# edit config.json — set workspace path, storage account, ceiling
.\bootstrap.ps1
```

That registers the scheduled tasks, drops the memory templates into the spot your editor's memory tool reads from, and runs a self-test of the spend gate.

## What's not here yet

- The brain container (networked vector recall) — design notes in `brain/README.md`, full Docker image in v0.2.
- Bash / macOS bootstrap — coming with v0.2.
- Multi-agent coordination wedge (`claim` / `release` / `handoff`) — drops in on top of the brain layer; v0.3.

## License

MIT (see `LICENSE`). Use this however you want. Attribution to **Recall™** appreciated.

## Why "Recall"?

Because the whole architecture is built around one question: *what does the agent recall when it sits down tomorrow?* If the answer is "whatever VS Code felt like keeping," you have a problem. Recall makes the answer "exactly what you wrote down on purpose."

— Steve Paltridge · <https://recall.works>

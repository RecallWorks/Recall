# Recall · Agent OS — bin/

Reference implementation scripts. PowerShell 7+, no dependencies beyond what
your platform already needs (Azure CLI for vault scripts, ollama for qwen
scripts).

Every script:

- reads `config.json` from the repo root (or the path passed via `-Config`)
- honors a kill-switch file (path defined in `config.json`)
- can run in `-DryRun` mode where applicable
- exits non-zero on any failure (fail-closed)

| Script                       | Purpose                                                          | Status |
|------------------------------|------------------------------------------------------------------|--------|
| `spend-gate.ps1`             | Provider-side cost ceiling check (fail-closed)                   | READY  |
| `vault-sync.ps1`             | Nightly snapshot of workspace + memory dir to draft container    | READY  |
| `vault-promote.ps1`          | Weekly sweep of >N-day draft blobs into WORM vault container     | READY  |
| `brain-snapshot.ps1`         | Weekly zip of brain state → vault + sealed local copy            | READY  |
| `mark-touched.ps1`           | Log a folder so vault-sync picks it up next run                  | READY  |
| `transcript-tail.ps1`        | Locate active editor transcript and emit last N KB               | READY  |
| `qwen-rolling-summary.ps1`   | Periodic local-model summary of active session → memory dir      | READY  |
| `qwen-coldstart.ps1`         | One-shot orientation brief from memory + newest revival doc      | READY  |
| `latest-revival.ps1`         | Print newest revival doc, qwen-compressed if >24h old            | READY  |

## Conventions

- All `*.ps1` files take a `-Config <path>` parameter (default: `..\config.json`).
- All log files land under `..\logs\` (gitignored).
- All state files (last-call timestamps, etc.) land under `..\state\`.
- All scripts accept `-DryRun` where it makes sense.

## Adapting to your environment

The originals at `c:\Dev\tools\` (in the originating workstation) had hard-coded
paths and account names. The public versions read everything from `config.json`.

If you're porting these to bash/zsh, the public-facing logic is intentionally
small — each script under 200 lines. The PowerShell sugar is mostly
`Invoke-RestMethod` and `azcopy` orchestration.

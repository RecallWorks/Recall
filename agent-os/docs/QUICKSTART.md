# Quickstart

## Prereqs

- **PowerShell 7+** (cross-platform).
- **ollama** with at least one local model pulled (default: `qwen2.5-coder:14b`).
- **Azure CLI** (`az`) + **azcopy** if you're using the reference Azure Blob
  vault. If you're rolling your own object-storage backend, you can skip these
  and adapt `bin/vault-sync.ps1` accordingly.
- A coding agent host whose memory directory you control (e.g. GitHub Copilot
  Chat under VS Code; the path is in `config.example.json`).

## 60-second install

```powershell
git clone https://github.com/recall-works/agent-os
cd agent-os
cp config.example.json config.json
# 1) edit config.json — fill in workspaceId + storageAccount at minimum
# 2) put your storage key into config/.vault-key.txt as: KEY=<key>
.\bootstrap.ps1
```

`bootstrap.ps1` is idempotent. First run creates `config.json` from the
example and stops so you can edit. Second run does the real work.

## What just happened

- `state/` and `logs/` directories created at the repo root.
- Templates from `templates/` copied into your agent's memory directory
  (skipped if files already exist there — destructive overwrites do not happen).
- `spend-gate.ps1` self-test ran (verifies your provider auth + cost API access).
- Scheduled tasks registered:
  - `Recall-VaultSync-Nightly` — daily 2 AM
  - `Recall-VaultPromote-Weekly` — weekly Sunday 3 AM
  - `Recall-BrainSnapshot-Weekly` — weekly Sunday 4 AM
  - `Recall-RollingSummary-Q` — every 15 min, idempotent on transcript growth

## First-day usage

After bootstrap, your day-to-day workflow is the agent's, not yours. The
scheduled tasks run on their own. The memory dir templates feed the agent
durable context every conversation.

If you want to verify, manually:

```powershell
pwsh ./bin/vault-sync.ps1 -DryRun
pwsh ./bin/qwen-coldstart.ps1 -Save
```

The first dry-runs the nightly snapshot (no data written). The second
generates `_coldstart-brief.md` in your memory dir — open the agent and
ask it to summarize the brief; you'll see it react to durable context.

## Verification checklist

- [ ] `config.json` exists and is **not** committed (it's gitignored).
- [ ] `config/.vault-key.txt` exists, contains `KEY=<your key>`, **not** committed.
- [ ] Memory dir contains `00-routing.md`, `05-audit-trail.md` etc.
- [ ] `state/.spend-gate-last` was written by the self-test.
- [ ] Scheduled tasks visible in Task Scheduler under names starting with `Recall-`.

## Cost expectation

Per the whitepaper (`/site/agent-os.html`), all-in monthly cost for a single
workstation running this stack: **under $1/mo** in the reference Azure Blob
vault tier. The local model is free. Your bandwidth is whatever the nightly
snapshot pulls (typically 50-200 MB after the first full sync).

## When to read what

- Stuck on something? Read `templates/fix-at-root-reflex.md.tmpl` — it's the
  habit that pays the highest dividends.
- Adding a new external folder to backups? Use `bin/mark-touched.ps1`.
- Brain went sideways? Read `brain/README.md` and the
  `agency_sidecar_patch.md` design note.

## Uninstall

```powershell
# Remove scheduled tasks
Get-ScheduledTask -TaskName 'Recall-*' | Unregister-ScheduledTask -Confirm:$false

# Remove repo
Remove-Item -Recurse -Force <path-to-agent-os>

# Vault data (if you want to fully clean up)
# - draft container: free to delete
# - vault container: time-locked WORM, you cannot delete until lock expires
# - sealed local backups under state/sealed-brain-backups/: rename .SEALED.zip -> .zip first
```

The vault container's WORM policy is the only thing the uninstall **can't**
clean up immediately, by design. That's the point of the policy.

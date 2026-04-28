<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | scope notes for two gated workstreams; agent does NO work until Steve picks one -->
# Gated Workstreams — Next Actions

Both items below are referenced in [`/memories/05-audit-trail.md`](file:///c%3A/Users/StevePaltridge/AppData/Roaming/Code/User/globalStorage/github.copilot-chat/memory/05-audit-trail.md)
as "Steve-gated". Agent has done **zero work** on either; this file just
captures the scope so picking one up later is fast.

## SettingsPilot batch-9

- **Where**: `C:\Dev\EncompassSettingsPlugin\schema-extract\generate-batch9.ps1` (to be created); recipes land in `C:\Dev\EncompassSettingsPlugin\_pending-batch9\`.
- **Predecessor**: batch-8 (per memory `S-20260422-batch8`) shipped 50 read-only recipes targeting uncovered `ConfigManager`/`OrgManager`/`BpmManager`/`ServerManager` methods using probe v3.0 reflection dumps.
- **Inputs ready**: `_probe-iconfig-methods.json`, `_probe-ibpm-methods.json`, `_probe-iorg-methods.json`, `_probe-iserver-methods.json` (1020 manager method signatures total).
- **Verb-allowlist guard**: must filter to read-only verbs (`Get|List|Read|Find|Query|Count|Has|Is|Can|Calculate`). Batch-8 blocked 436 mutating-verb method calls.
- **Coverage target**: get from current 226/323 deep-probe keys (70%) to 90% — needs ~65 new probe-eligible methods after dedup vs batch-8.
- **Validation path**: ICE Encompass FormBuilder → Tools → Package Import Wizard → install .empkg → form reopen → export results JSON → diff vs prior batch.
- **Blocker**: batch-9 needs PluginAudit ClientContext blocker resolved first per memory `S-20260422-pluginaudit` ("Server.dll statics") — otherwise probe v3.0 is the ceiling.
- **Owner gate**: Steve confirms (a) priority vs other lender outreach, (b) acceptable to ship recipe-only update without resolving ClientContext blocker (i.e. ship at 80% coverage).

## IceWhisperer Edge variant

- **Where**: New `IceWhisperer/extension/edge/` sibling to existing `IceWhisperer/extension/` (Chrome MV3).
- **Status**: Existing extension is Chrome MV3 with Firefox compat shipped this session (per prior batch B+C+D+E+F summary in conversation history — `extension/firefox/` exists).
- **Edge specifics**:
  1. Edge is Chromium-based — most MV3 manifest is identical.
  2. Differs in: extension store submission (Microsoft Partner Center, not CWS), `update_url` field in manifest, optional `browser_specific_settings` for legacy compat.
  3. No code changes likely needed in `background.js`/`content.js`/`popup.*`. Just a separate manifest + store listing.
- **Deliverable**: `extension/edge/manifest.json` + `extension/edge/README.md` describing Microsoft Partner Center submission flow + screenshots.
- **Owner gate**: Steve confirms whether Edge is worth the dual-listing maintenance burden vs telling Edge users "install from Chrome Web Store" (Edge supports CWS extensions natively since 2020).

## Items NOT in this list (deliberately)

- **Channel-brain endpoint deploy** — Rule 4 forbids deploy without explicit per-deploy approval. Steve must say "deploy" before any `azd up`/`func publish`/`docker push`.
- **Real Chrome load test** — needs interactive browser; agent cannot drive.
- **Outside-counsel call** — see [`outside-counsel-checklist.md`](./outside-counsel-checklist.md). Steve schedules.

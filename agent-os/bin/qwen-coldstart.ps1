# @recall.works/agent-os | qwen-coldstart.ps1 | v1.0
# Generate a cold-start orientation brief from active memory + newest revival
# doc, using the local model. Zero user-tokens.
#
# Usage:
#   pwsh ./qwen-coldstart.ps1                # generic brief, prints to stdout
#   pwsh ./qwen-coldstart.ps1 -Topic foo     # topic-focused
#   pwsh ./qwen-coldstart.ps1 -Save          # write to memories/_coldstart-brief.md

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json'),
    [string] $Topic  = '',
    [switch] $Save
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json

$memDir = [System.Environment]::ExpandEnvironmentVariables($cfg.memory.memoriesDir)
if (-not (Test-Path $memDir)) { Write-Error "memory dir missing: $memDir"; exit 3 }

# State-bearing files only (skip protocol/anti-pattern reference files)
$stateFiles = @('00-routing.md','03-preferences.md','05-audit-trail.md')
$mems = $stateFiles | ForEach-Object { Get-Item (Join-Path $memDir $_) -ErrorAction SilentlyContinue } | Where-Object { $_ }

$memBlob = ($mems | ForEach-Object {
    $body = Get-Content $_.FullName -Raw
    if ($_.Name -eq '05-audit-trail.md') {
        $rows = ($body -split "`n") | Where-Object { $_ -match '^\| S-' }
        $tail = $rows | Select-Object -First 40
        $body = "<header trimmed>`n" + ($tail -join "`n")
    }
    "===== $($_.Name) =====`n$body"
}) -join "`n`n"

# Newest revival doc
$revBlob = ''
$revDir = Join-Path ([System.Environment]::ExpandEnvironmentVariables($cfg.workspace.primary)) 'REVIVAL'
if (Test-Path $revDir) {
    $pat = if ($Topic) { "REVIVAL-S*-$Topic*.md" } else { 'REVIVAL-S*.md' }
    $newest = Get-ChildItem $revDir -Filter $pat |
        Where-Object { $_.Name -notmatch '\.compact\.md$' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($newest) {
        $revBlob = "===== NEWEST REVIVAL ($($newest.Name)) =====`n$(Get-Content $newest.FullName -Raw)"
    }
}

$intent = if ($Topic) { "topic-focused cold-start brief for: $Topic" } else { "generic cold-start brief across all active workstreams" }

$prompt = @"
You are generating a cold-start orientation brief for an AI agent that is about to
start a session. The agent already has hard guardrails. You produce only the
"what's currently going on" digest.

INTENT: $intent

OUTPUT — exactly these sections, in order, telegraphese throughout:
## active sessions
- one bullet per OPEN session in audit-trail. format: S-id | agent | 1-line state.
- 5-8 bullets max. newest first.

## current focus
- 1-3 bullets. what is the agent likely walking into? cite REVIVAL doc + S-id.

## recent decisions (last 7 days)
- bullets of architecture/preference choices that future-me must honor.

## blockers / gotchas
- bullets of failure modes flagged in REVIVAL or audit. include untested callouts.

## tools to remember
- 3-5 bullets of scripts, commands, file paths the agent will reach for.

RULES:
- Drop articles/pronouns. Use → + : ; symbols. PRESERVE: file paths, hex sigs, version numbers, identifiers, REVIVAL-* refs.
- 60 lines max total.
- No preamble. No code fences. Start with "## active sessions".

INPUT:
$memBlob

$revBlob
"@

$payload = @{
    model = $cfg.localModel.model
    prompt = $prompt
    stream = $false
    options = @{ temperature = 0.15; num_ctx = 32768; num_predict = 1200 }
} | ConvertTo-Json -Depth 5 -Compress

try {
    $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 300
    $brief = $resp.response.Trim()
} catch {
    Write-Error "qwen call failed: $($_.Exception.Message)"
    exit 4
}

$header = "<!-- coldstart-brief | $(Get-Date -Format 'yyyy-MM-dd HH:mm') | topic=$Topic -->`n"
$out = $header + $brief

if ($Save) {
    $savePath = Join-Path $memDir '_coldstart-brief.md'
    $out | Set-Content -Path $savePath -Encoding UTF8
    Write-Host "wrote $savePath ($($out.Length) chars)"
} else {
    Write-Output $out
}

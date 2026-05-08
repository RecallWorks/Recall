# @recall.works/agent-os | qwen-rolling-summary.ps1 | v1.0
# Periodic local-model summarization of the active session transcript into a
# durable markdown file under the agent's memory dir. Zero cost (local model),
# zero user-tokens.
#
# Usage:  pwsh ./qwen-rolling-summary.ps1 [-Config ../config.json] [-Force]
#
# Idempotent: skips if the transcript hasn't grown by `MinGrowthKB` since last run.

[CmdletBinding()]
param(
    [string] $Config       = (Join-Path $PSScriptRoot '..\config.json'),
    [int]    $TailKB       = 80,
    [int]    $MinGrowthKB  = 20,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$repoRoot = Split-Path $Config

$kill = Join-Path $repoRoot $cfg.localModel.killSwitchFile
if (Test-Path $kill) { Write-Error "qwen-rolling-summary ABORT: kill switch present"; exit 99 }

$ollama = (Get-Command ollama -ErrorAction SilentlyContinue).Source
if (-not $ollama) { Write-Error "ollama not on PATH"; exit 3 }
$model = $cfg.localModel.model

# --- locate active transcript ---
$tdir = [System.Environment]::ExpandEnvironmentVariables(
    $cfg.memory.transcriptsDir.Replace('<workspaceId>', $cfg.memory.workspaceId)
)
if (-not (Test-Path $tdir)) { Write-Error "transcripts dir missing: $tdir"; exit 4 }
$active = Get-ChildItem $tdir -Filter *.jsonl -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $active) { Write-Host "[rolling-summary] no transcript yet"; exit 0 }
$sid = [System.IO.Path]::GetFileNameWithoutExtension($active.Name)

# --- output target (memory dir, session subdir) ---
$memDir = [System.Environment]::ExpandEnvironmentVariables($cfg.memory.memoriesDir)
$outDir = Join-Path $memDir 'session'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outFile = Join-Path $outDir "$sid-rolling.md"

$stateDir = Join-Path $repoRoot 'state'
if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
$stateFile = Join-Path $stateDir "rolling-summary-$sid.state"

# --- growth check ---
$currentMark = "$($active.LastWriteTimeUtc.Ticks):$($active.Length)"
if (-not $Force -and (Test-Path $stateFile)) {
    $prev = (Get-Content $stateFile -Raw).Trim()
    if ($prev) {
        $prevSize = [int64]($prev -split ':')[1]
        $growKB = ($active.Length - $prevSize) / 1KB
        if ($growKB -lt $MinGrowthKB) {
            Write-Host "[rolling-summary] skip — grew $([math]::Round($growKB,1)) KB (threshold $MinGrowthKB)"
            exit 0
        }
    }
}

# --- pull tail ---
$tailFile = Join-Path $env:TEMP "transcript-tail-$sid.jsonl"
& (Join-Path $PSScriptRoot 'transcript-tail.ps1') -Config $Config -TailKB $TailKB -OutFile $tailFile | Out-Null
if (-not (Test-Path $tailFile)) { Write-Error "tail not produced"; exit 5 }
$tailText = Get-Content $tailFile -Raw -Encoding UTF8
$tailText = [regex]::Replace($tailText, "\x1b\[[0-9;]*[A-Za-z]", '')
$tailText = [regex]::Replace($tailText, '[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '')

# --- pre-extract conversational turns (user.message/assistant.message + selected tool calls) ---
$turns = New-Object System.Collections.Generic.List[string]
foreach ($line in ($tailText -split "`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $obj = $line | ConvertFrom-Json -ErrorAction Stop } catch { continue }
    switch ($obj.type) {
        'user.message' {
            $c = $obj.data.content
            if ($c -and $c.Trim()) { $turns.Add("USER: $($c.Trim())") }
        }
        'assistant.message' {
            $c = $obj.data.content
            if ($c -and $c.Trim()) { $turns.Add("ASSISTANT: $($c.Trim())") }
            if ($obj.data.toolRequests) {
                foreach ($tr in $obj.data.toolRequests) {
                    if ($tr.name -in 'run_in_terminal','create_file','replace_string_in_file','multi_replace_string_in_file') {
                        try {
                            $a = $tr.arguments | ConvertFrom-Json -ErrorAction Stop
                            $hint = $a.command
                            if (-not $hint) { $hint = $a.filePath }
                            if (-not $hint) { $hint = $a.explanation }
                            if ($hint) {
                                $oneline = ($hint -replace '\s+',' ')
                                $entry = "TOOL[$($tr.name)]: $oneline"
                                if ($entry.Length -gt 300) { $entry = $entry.Substring(0,300) }
                                $turns.Add($entry)
                            }
                        } catch {}
                    }
                }
            }
        }
    }
}
$dialogue = ($turns -join "`n`n")
if (-not $dialogue) { Write-Warning "no conversational turns extracted"; exit 6 }

$prompt = @"
You are a session archivist. Below is a USER/ASSISTANT dialogue with selected
TOOL calls noted inline. Produce ONLY a structured markdown summary using these
EXACT headings, in this order:

## Verbatim user directives
## Decisions made
## Files touched
## Open threads
## Last operational state

Rules:
- Quote the user's exact words for any directives. Keep quotes short.
- Preserve exact paths, version numbers, identifiers verbatim.
- For "Files touched" list paths from TOOL[create_file]/TOOL[replace_string_in_file]/TOOL[multi_replace_string_in_file] entries.
- If a section has nothing, write `(none)` under it.
- Do NOT echo raw input. Do NOT add a preamble. Do NOT refuse.
- Total output under 1500 words.

DIALOGUE:
$dialogue
"@

$tmpPrompt = Join-Path $env:TEMP "rolling-prompt-$sid.txt"
[System.IO.File]::WriteAllText($tmpPrompt, $prompt, [System.Text.UTF8Encoding]::new($false))

$start = Get-Date
$errLog = Join-Path $env:TEMP "rolling-stderr-$sid.log"
$body = Get-Content $tmpPrompt -Raw -Encoding UTF8 | & $ollama run $model 2>$errLog
$elapsed = ((Get-Date) - $start).TotalSeconds

if (-not $body -or ($body -join '').Trim().Length -lt 50) {
    Write-Warning "qwen returned empty/near-empty (prompt $([math]::Round((Get-Item $tmpPrompt).Length/1KB,1)) KB)"
    if (Test-Path $errLog) { Get-Content $errLog -Tail 5 | ForEach-Object { Write-Warning "  $_" } }
    exit 7
}

$now = Get-Date
$header = @"
<!-- recall.works/agent-os | rolling-summary | $($now.ToString('yyyy-MM-dd HH:mm')) | session $sid -->
<!-- Source: $($active.FullName) | tail $TailKB KB | model $model | $([math]::Round($elapsed,1))s -->

# Rolling Summary — session $sid

_Last updated: $($now.ToString('yyyy-MM-dd HH:mm:ss')) · transcript $([math]::Round($active.Length/1KB,1)) KB_

"@

[System.IO.File]::WriteAllText($outFile, $header + ($body -join "`n"), [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($stateFile, $currentMark, [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    Session       = $sid
    OutFile       = $outFile
    QwenSeconds   = [math]::Round($elapsed,1)
    SummaryBytes  = (Get-Item $outFile).Length
    TranscriptKB  = [math]::Round($active.Length/1KB,1)
}

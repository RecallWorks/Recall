# @recall.works/agent-os | bootstrap.ps1 | v1.0
# Windows installer. Idempotent. Re-run safely.
#
#   1. Verifies dependencies (PowerShell 7+, ollama, az, azcopy).
#   2. Verifies config.json exists (created from example if missing).
#   3. Creates state/ and logs/ directories.
#   4. Copies template files into the agent's memory dir (skips existing).
#   5. Self-tests spend-gate (fails the install if it can't pass).
#   6. Registers scheduled tasks per config.schedules.
#
# Usage:  pwsh ./bootstrap.ps1 [-Config ./config.json] [-SkipTasks] [-WhatIf]

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot 'config.json'),
    [switch] $SkipTasks
)

$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot

Write-Host '=== Recall · Agent OS bootstrap ===' -ForegroundColor Cyan

# --- step 1: dependencies ---
function Need($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) { Write-Error "missing dependency: $name (install it and re-run)"; exit 2 }
    "  ok   $name -> $($cmd.Source)"
}
'checking dependencies...'
Need pwsh
Need ollama
Need az
Need azcopy

# --- step 2: config ---
if (-not (Test-Path $Config)) {
    $example = Join-Path $repoRoot 'config.example.json'
    if (-not (Test-Path $example)) { Write-Error "config.example.json missing"; exit 3 }
    Copy-Item $example $Config
    Write-Host "  created $Config (from example) — EDIT IT before continuing." -ForegroundColor Yellow
    Write-Host '  re-run bootstrap.ps1 once the config is filled in.' -ForegroundColor Yellow
    exit 0
}
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
"  ok   config: $Config"

# --- step 3: directories ---
foreach ($d in @('state','logs','config')) {
    $p = Join-Path $repoRoot $d
    if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}
"  ok   state/ logs/ config/"

# --- step 4: copy templates into agent memory dir ---
$memDir = [System.Environment]::ExpandEnvironmentVariables($cfg.memory.memoriesDir)
if (-not (Test-Path $memDir)) {
    Write-Host "  warn memory dir does not exist yet: $memDir" -ForegroundColor Yellow
    Write-Host "       create it (or open the editor's chat once) and re-run, or pre-create:" -ForegroundColor Yellow
    Write-Host "       New-Item -ItemType Directory -Path '$memDir' -Force" -ForegroundColor Yellow
} else {
    $tdir = Join-Path $repoRoot 'templates'
    Get-ChildItem $tdir -File | ForEach-Object {
        $dest = Join-Path $memDir ($_.Name -replace '\.tmpl$','')
        if (-not (Test-Path $dest)) {
            Copy-Item $_.FullName $dest
            "  copied template: $($_.Name) -> $dest"
        } else {
            "  skip (exists):    $dest"
        }
    }
}

# --- step 5: spend-gate self-test ---
'self-testing spend-gate...'
& (Join-Path $repoRoot 'bin\spend-gate.ps1') -Config $Config -Quiet
if ($LASTEXITCODE -ne 0) { Write-Error "  spend-gate failed (exit $LASTEXITCODE). Fix and re-run."; exit 4 }
"  ok   spend-gate"

# --- step 6: scheduled tasks ---
if ($SkipTasks) {
    "skipped scheduled task registration (-SkipTasks)"
    Write-Host '=== bootstrap done ===' -ForegroundColor Cyan
    exit 0
}

function Add-DailyTask([string]$name, [string]$script, [string]$cronTime) {
    # cronTime like "0 2 * * *" -> hour 2 daily; we use a tiny parser
    $parts = $cronTime.Split(' ')
    $hour = [int]$parts[1]; $minute = [int]$parts[0]
    $when = (Get-Date).Date.AddHours($hour).AddMinutes($minute)
    $action  = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoProfile -File `"$script`" -Config `"$Config`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $when
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    "  task registered: $name @ $($when.ToString('HH:mm')) daily"
}
function Add-WeeklyTask([string]$name, [string]$script, [string]$cronTime) {
    $parts = $cronTime.Split(' ')
    $hour = [int]$parts[1]; $minute = [int]$parts[0]
    $dow = $parts[4]  # "0" = Sunday
    $dowName = @('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')[[int]$dow]
    $when = (Get-Date).Date.AddHours($hour).AddMinutes($minute)
    $action  = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoProfile -File `"$script`" -Config `"$Config`""
    $trigger = New-ScheduledTaskTrigger -Weekly -At $when -DaysOfWeek $dowName
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    "  task registered: $name @ $($dowName) $($when.ToString('HH:mm'))"
}
function Add-RepeatingTask([string]$name, [string]$script, [int]$minutes) {
    $action  = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NoProfile -File `"$script`" -Config `"$Config`""
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes $minutes)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    "  task registered: $name every $minutes min"
}

$bin = Join-Path $repoRoot 'bin'
Add-DailyTask     'Recall-VaultSync-Nightly'    (Join-Path $bin 'vault-sync.ps1')           $cfg.schedules.vaultSyncCron
Add-WeeklyTask    'Recall-VaultPromote-Weekly'  (Join-Path $bin 'vault-promote.ps1')        $cfg.schedules.vaultPromoteCron
Add-WeeklyTask    'Recall-BrainSnapshot-Weekly' (Join-Path $bin 'brain-snapshot.ps1')       $cfg.schedules.brainSnapshotCron
Add-RepeatingTask 'Recall-RollingSummary-Q'     (Join-Path $bin 'qwen-rolling-summary.ps1') $cfg.schedules.rollingSummaryEveryMinutes

Write-Host '=== bootstrap done ===' -ForegroundColor Cyan
Write-Host 'Next:'
Write-Host '  1. Verify config.json — workspaceId, storageAccount, etc.'
Write-Host '  2. Run: pwsh ./bin/qwen-coldstart.ps1 -Config ./config.json -Save'
Write-Host '  3. Read your editor''s memory dir to confirm templates landed.'

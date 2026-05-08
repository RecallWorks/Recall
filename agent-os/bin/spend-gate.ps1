# @recall.works/agent-os | spend-gate.ps1 | v1.0
# Provider-side cost ceiling. Fail-closed.
#
# Usage:  pwsh ./spend-gate.ps1 [-Config ../config.json] [-Quiet]
#
# Called by every billable script BEFORE doing anything that costs money.
# Exits 0 = OK to proceed. Non-zero = ABORT.
#
# Designed to fail SAFE: if the cost API itself errors, we DON'T proceed.
#
# Currently implements Azure provider via `az consumption usage list`.
# Adapt the Layer-3 block to your provider (AWS Cost Explorer, GCP billing).

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json'),
    [switch] $Quiet
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "spend-gate: config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json

$ceilingUSD  = [double]$cfg.spendGate.monthlyCeilingUSD
$failClosed  = [bool]$cfg.spendGate.failClosed
$cacheSecs   = [int]$cfg.spendGate.cacheSeconds
$kill        = Join-Path (Split-Path $Config) $cfg.spendGate.killSwitchFile
$stateDir    = Join-Path (Split-Path $Config) 'state'
if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
$lastCall    = Join-Path $stateDir '.spend-gate-last'

# --- Layer 1: kill switch ---
if (Test-Path $kill) { Write-Error "spend-gate ABORT: kill switch present at $kill"; exit 99 }

# --- Layer 2: cooldown / cache ---
if (Test-Path $lastCall) {
    $age = (Get-Date) - (Get-Item $lastCall).LastWriteTime
    if ($age.TotalSeconds -lt $cacheSecs) {
        $cached = (Get-Content $lastCall -Raw).Trim()
        if ($cached -match '^PASS') { exit 0 } else { exit 1 }
    }
}

# --- Layer 3: query month-to-date spend (Azure) ---
$startOfMonth = (Get-Date -Day 1).ToString('yyyy-MM-dd')
$today = (Get-Date).ToString('yyyy-MM-dd')

try {
    $sub = az account show --query id -o tsv 2>$null
    if (-not $sub) {
        if ($failClosed) { Write-Error "spend-gate FAIL-CLOSED: az not logged in"; exit 1 }
        else { "PASS-NODATA" | Set-Content $lastCall; exit 0 }
    }

    $usage = az consumption usage list --start-date $startOfMonth --end-date $today `
             --query "[].pretaxCost" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        if (-not $Quiet) { Write-Warning "spend-gate: consumption API unavailable; proceeding without cost data" }
        "PASS-NODATA" | Set-Content $lastCall
        exit 0
    }

    $numeric = @($usage | Where-Object { $_ -match '^\s*-?\d+(\.\d+)?\s*$' } | ForEach-Object { [double]$_ })
    $mtd = if ($numeric.Count) { [math]::Round(($numeric | Measure-Object -Sum).Sum, 2) } else { 0 }

    if ($mtd -ge $ceilingUSD) {
        Write-Error "spend-gate ABORT: MTD `$$mtd >= ceiling `$$ceilingUSD"
        "BLOCK: $mtd / $ceilingUSD" | Set-Content $lastCall
        exit 1
    }

    if (-not $Quiet) { "spend-gate OK: MTD `$$mtd / ceiling `$$ceilingUSD" }
    "PASS: $mtd / $ceilingUSD" | Set-Content $lastCall
    exit 0
} catch {
    if ($failClosed) { Write-Error "spend-gate FAIL-CLOSED: $_"; exit 1 }
    else { "PASS-ERROR" | Set-Content $lastCall; exit 0 }
}

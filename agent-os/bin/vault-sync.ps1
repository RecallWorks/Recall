# @recall.works/agent-os | vault-sync.ps1 | v1.0
# Snapshot workspace + agent memory dir to a "draft" object-storage container.
# Designed to run nightly. Cool tier; promotion to WORM happens via vault-promote.ps1.
#
# Usage:  pwsh ./vault-sync.ps1 [-Config ../config.json] [-DryRun]
#
# Provider: Azure Blob Storage (azcopy + az). To use AWS S3, swap the SAS
# generation block for a presigned URL and replace `azcopy sync` with
# `aws s3 sync`. The structure is the same.

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json'),
    [switch] $DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "vault-sync: config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$repoRoot = Split-Path $Config

# --- gates ---
$kill = Join-Path $repoRoot $cfg.spendGate.killSwitchFile
if (Test-Path $kill) { Write-Error "vault-sync ABORT: kill switch present"; exit 99 }
& (Join-Path $PSScriptRoot 'spend-gate.ps1') -Config $Config -Quiet
if ($LASTEXITCODE -ne 0 -and -not $DryRun) { Write-Error "vault-sync ABORT: spend-gate denied"; exit 98 }

# --- inputs ---
$primary = [System.Environment]::ExpandEnvironmentVariables($cfg.workspace.primary)
$memDir  = [System.Environment]::ExpandEnvironmentVariables($cfg.memory.memoriesDir)
$mcpJson = Join-Path $env:APPDATA 'Code\User\mcp.json'

$SOURCES = @(
    @{ Local = $primary; Prefix = 'workspace' }
    @{ Local = $memDir;  Prefix = 'memories'  }
)
if (Test-Path $mcpJson) { $SOURCES += @{ Local = $mcpJson; Prefix = 'mcp-config' } }

# Touched-folder log (companion to mark-touched.ps1)
$touchedLog = Join-Path $repoRoot 'state\agent-touched-folders.log'
if (Test-Path $touchedLog) {
    Get-Content $touchedLog | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object {
        $line = ($_ -split '#',2)[0].Trim()
        if ($line -and (Test-Path $line)) {
            $prefix = ($line -replace '[:\\/ ]', '_').Trim('_').ToLower()
            if ($prefix.Length -gt 60) { $prefix = $prefix.Substring($prefix.Length - 60) }
            $SOURCES += @{ Local = $line; Prefix = "touched/$prefix" }
        }
    }
}

# --- credentials ---
$SA        = $cfg.vault.storageAccount
$container = $cfg.vault.draftContainer
$keyFile   = Join-Path $repoRoot $cfg.vault.keyFile
if (-not (Test-Path $keyFile)) { Write-Error "vault-sync: key file missing: $keyFile"; exit 3 }
$KEY = (Get-Content $keyFile -Raw).Trim() -replace '^KEY=',''

$expiry = (Get-Date).ToUniversalTime().AddHours(24).ToString('yyyy-MM-ddTHH:mm:ssZ')
$sas = az storage container generate-sas --account-name $SA --account-key $KEY --name $container `
       --permissions rwdlc --expiry $expiry --https-only -o tsv
if (-not $sas) { Write-Error "vault-sync: SAS generation failed"; exit 4 }

# --- log ---
$logDir = Join-Path $repoRoot 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$log = Join-Path $logDir "sync-$ts.log"

$excludePatterns = '*.lock;*.pid;~$*;Thumbs.db;.DS_Store'
$totalErrors = 0

foreach ($src in $SOURCES) {
    if (-not (Test-Path $src.Local)) {
        "SKIP missing: $($src.Local)" | Tee-Object -FilePath $log -Append
        continue
    }
    $remote = "https://$SA.blob.core.windows.net/$container/$($src.Prefix)?$sas"
    $isFile = -not (Get-Item $src.Local).PSIsContainer

    if ($isFile) {
        $azArgs = @('copy', $src.Local, $remote, '--overwrite=ifSourceNewer')
    } else {
        $azArgs = @('sync', $src.Local, $remote, '--recursive', '--exclude-pattern', $excludePatterns, '--delete-destination=false')
    }
    if ($DryRun) { $azArgs += '--dry-run' }

    "==== $($src.Prefix) <- $($src.Local) ====" | Tee-Object -FilePath $log -Append
    & azcopy @azArgs 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) { $totalErrors++ }
}

"==== sync complete | sources=$($SOURCES.Count) | errors=$totalErrors | log=$log ====" | Tee-Object -FilePath $log -Append
exit $totalErrors

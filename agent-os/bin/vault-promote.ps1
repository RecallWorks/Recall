# @recall.works/agent-os | vault-promote.ps1 | v1.0
# Sweep blobs older than N days from the mutable "draft" container into the
# WORM "vault" container, then delete the draft copy. Resume-safe.
#
# Usage:  pwsh ./vault-promote.ps1 [-Config ../config.json] [-DaysOld 30] [-DryRun]
#
# This is the only script in the system that issues a delete, and it deletes
# only against draft. The vault container has time-based immutability set at
# the platform layer; the cloud refuses delete attempts there regardless of
# permissions. Belt + suspenders.

[CmdletBinding()]
param(
    [string] $Config  = (Join-Path $PSScriptRoot '..\config.json'),
    [int]    $DaysOld = 30,
    [switch] $DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$repoRoot = Split-Path $Config

# --- gates ---
$kill = Join-Path $repoRoot $cfg.spendGate.killSwitchFile
if (Test-Path $kill) { Write-Error "vault-promote ABORT: kill switch present"; exit 99 }
& (Join-Path $PSScriptRoot 'spend-gate.ps1') -Config $Config -Quiet
if ($LASTEXITCODE -ne 0 -and -not $DryRun) { Write-Error "vault-promote ABORT: spend-gate denied"; exit 98 }

# --- log ---
$logDir = Join-Path $repoRoot 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$log = Join-Path $logDir "promote-$ts.log"
Start-Transcript -Path $log -Append | Out-Null

try {
    $SA       = $cfg.vault.storageAccount
    $draft    = $cfg.vault.draftContainer
    $vault    = $cfg.vault.vaultContainer
    $keyFile  = Join-Path $repoRoot $cfg.vault.keyFile
    if (-not (Test-Path $keyFile)) { Write-Error "key file missing: $keyFile"; exit 3 }
    $KEY = (Get-Content $keyFile -Raw).Trim() -replace '^KEY=',''

    $cutoff = (Get-Date).ToUniversalTime().AddDays(-$DaysOld)
    "== promote $draft -> $vault | older than $DaysOld days ($($cutoff.ToString('yyyy-MM-dd'))) =="

    $blobs = az storage blob list --account-name $SA --account-key $KEY --container-name $draft `
        --query "[].{name:name, lastModified:properties.lastModified, size:properties.contentLength}" -o json | ConvertFrom-Json
    $old = @($blobs | Where-Object { [datetime]$_.lastModified -lt $cutoff })
    "found $($blobs.Count) draft blobs ; $($old.Count) eligible for promotion"

    if ($old.Count -eq 0) { return }

    "indexing vault container for resume-safety..."
    $vaultBlobs = az storage blob list --account-name $SA --account-key $KEY --container-name $vault `
        --query "[].name" -o tsv
    $vaultSet = @{}
    foreach ($n in $vaultBlobs) { if ($n) { $vaultSet[$n] = $true } }

    if ($DryRun) {
        $already = @($old | Where-Object { $vaultSet.ContainsKey($_.name) }).Count
        "[dry-run] candidates=$($old.Count) | already-in-vault=$already | would-copy=$($old.Count - $already)"
        return
    }

    $expiry = (Get-Date).ToUniversalTime().AddHours(2).ToString('yyyy-MM-ddTHH:mm:ssZ')
    $srcSas = az storage container generate-sas --account-name $SA --account-key $KEY --name $draft --permissions rl --expiry $expiry --https-only -o tsv
    $dstSas = az storage container generate-sas --account-name $SA --account-key $KEY --name $vault --permissions wc --expiry $expiry --https-only -o tsv

    $copied = 0; $skipped = 0; $failed = 0
    foreach ($b in $old) {
        if ($vaultSet.ContainsKey($b.name)) {
            az storage blob delete --account-name $SA --account-key $KEY --container-name $draft --name $b.name --delete-snapshots include 2>&1 | Out-Null
            $skipped++
            continue
        }
        $srcUrl = "https://$SA.blob.core.windows.net/$draft/$($b.name)?$srcSas"
        $dstUrl = "https://$SA.blob.core.windows.net/$vault/$($b.name)?$dstSas"
        $r = & azcopy copy $srcUrl $dstUrl --overwrite=false --log-level=ERROR 2>&1
        if ($LASTEXITCODE -eq 0) {
            az storage blob delete --account-name $SA --account-key $KEY --container-name $draft --name $b.name --delete-snapshots include 2>&1 | Out-Null
            $copied++
        } else {
            Write-Warning "failed: $($b.name) | $r"
            $failed++
        }
    }
    "== promote complete | promoted=$copied | skipped=$skipped | failed=$failed =="
} finally {
    Stop-Transcript | Out-Null
}

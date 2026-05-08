# @recall.works/agent-os | brain-snapshot.ps1 | v1.0
# Weekly zip of the brain's persistent state -> WORM vault + sealed local copy.
# The "brain" is whatever vector store you're running (ChromaDB, Qdrant, etc.).
# This script captures its data dir verbatim.
#
# Usage:  pwsh ./brain-snapshot.ps1 [-Config ../config.json] [-DryRun]

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json'),
    [switch] $DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$repoRoot = Split-Path $Config

$kill = Join-Path $repoRoot $cfg.spendGate.killSwitchFile
if (Test-Path $kill) { Write-Error "brain-snapshot ABORT: kill switch present"; exit 99 }
& (Join-Path $PSScriptRoot 'spend-gate.ps1') -Config $Config -Quiet
if ($LASTEXITCODE -ne 0 -and -not $DryRun) { Write-Error "brain-snapshot ABORT: spend-gate denied"; exit 98 }

# --- inputs ---
# By convention, brain state lives at <secondary>/brain/store or you set it explicitly.
$brainSrc = if ($cfg.brain.stateDir) {
    [System.Environment]::ExpandEnvironmentVariables($cfg.brain.stateDir)
} else {
    Join-Path ([System.Environment]::ExpandEnvironmentVariables($cfg.workspace.secondary)) 'brain\store'
}
if (-not (Test-Path $brainSrc)) { Write-Error "brain source not found: $brainSrc (set 'brain.stateDir' in config.json)"; exit 3 }

$sealedDir = Join-Path $repoRoot 'state\sealed-brain-backups'
if (-not (Test-Path $sealedDir)) { New-Item -ItemType Directory -Path $sealedDir -Force | Out-Null }

# Sentinel files
$donot = Join-Path $sealedDir 'DO-NOT-READ.txt'
if (-not (Test-Path $donot)) {
@'
SEALED COLD-STORAGE BRAIN BACKUPS.

DO NOT READ. DO NOT INDEX. DO NOT TREAT AS LIVE STATE.

These zips are renamed .SEALED.zip on purpose so the agent does not
mistake them for active brain content. Live brain is your container/
service. Authoritative cold-copy is in the WORM vault. These local zips
exist only as last-resort keepsake.

To restore: rename .SEALED.zip -> .zip, expand to a fresh location,
verify integrity manually before pointing services at it.
'@ | Set-Content -Path $donot -Encoding UTF8
}
'*' | Set-Content -Path (Join-Path $sealedDir '.gitignore') -Encoding ASCII

$ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$zipPath = Join-Path $sealedDir "brain-$ts.SEALED.zip"

"==== brain-snapshot $ts ===="
"src:    $brainSrc"
"sealed: $zipPath"

if ($DryRun) { "DRYRUN: would zip + upload + rotate"; exit 0 }

# Stage with excludes (.venv, __pycache__, *.tmp)
$tempStage = Join-Path $env:TEMP "brain-stage-$ts"
New-Item -ItemType Directory -Path $tempStage | Out-Null
$excludes = @('.venv','__pycache__','tmp','*.tmp')
robocopy $brainSrc $tempStage /E /XD ($excludes | ForEach-Object { Join-Path $brainSrc $_ }) /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Error "robocopy failed: $LASTEXITCODE"; Remove-Item $tempStage -Recurse -Force; exit 4 }

Compress-Archive -Path "$tempStage\*" -DestinationPath $zipPath -CompressionLevel Optimal
Remove-Item $tempStage -Recurse -Force

$zipMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
"sealed local: $zipPath ($zipMB MB)"

# Upload to vault
$SA      = $cfg.vault.storageAccount
$vault   = $cfg.vault.vaultContainer
$keyFile = Join-Path $repoRoot $cfg.vault.keyFile
$KEY = (Get-Content $keyFile -Raw).Trim() -replace '^KEY=',''
$expiry = (Get-Date).ToUniversalTime().AddHours(2).ToString('yyyy-MM-ddTHH:mm:ssZ')
$sas = az storage container generate-sas --account-name $SA --account-key $KEY --name $vault `
       --permissions rwc --expiry $expiry --https-only -o tsv
$remote = "https://$SA.blob.core.windows.net/$vault/brain/snap-$ts/brain.zip?$sas"
azcopy copy $zipPath $remote --log-level WARNING
if ($LASTEXITCODE -ne 0) { Write-Error "azcopy failed: $LASTEXITCODE"; exit 5 }
"vault uploaded: $vault/brain/snap-$ts/brain.zip"

# Rotate sealed local: keep newest 2
Get-ChildItem $sealedDir -Filter 'brain-*.SEALED.zip' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 2 |
    ForEach-Object { "rotating out (local): $($_.Name)"; Remove-Item $_.FullName -Force }

"==== brain-snapshot complete ===="

# @recall.works/agent-os | mark-touched.ps1 | v1.0
# Append a folder/file path to the touched-folders log so the next vault-sync
# run will back it up. Idempotent.
#
# Usage:
#   pwsh ./mark-touched.ps1 'C:\Some\External\Folder' [-Why "reason"]
#   pwsh ./mark-touched.ps1 ~/.config/something      [-Why "reason"]

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)] [string] $Path,
    [string] $Why = '',
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json')
)

$repoRoot = if (Test-Path $Config) { Split-Path $Config } else { Split-Path $PSScriptRoot }
$logFile = Join-Path $repoRoot 'state\agent-touched-folders.log'
if (-not (Test-Path (Split-Path $logFile))) { New-Item -ItemType Directory -Path (Split-Path $logFile) -Force | Out-Null }

$abs = (Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue).Path
if (-not $abs) { $abs = $Path }  # log even if doesn't exist yet

if (-not (Test-Path $logFile)) {
    @(
        '# agent-touched-folders.log',
        '# format: one absolute path per line. blank/# lines ignored.',
        '# vault-sync.ps1 reads this and backs up each path.',
        ''
    ) | Set-Content -Path $logFile -Encoding ASCII
}

$existing = Get-Content $logFile | Where-Object { $_ -and -not $_.StartsWith('#') } |
    ForEach-Object { ($_ -split '#',2)[0].Trim() }
if ($existing -contains $abs) { "already tracked: $abs"; return }

$comment = if ($Why) { "  # $Why ($(Get-Date -Format 'yyyy-MM-dd'))" } else { "  # ($(Get-Date -Format 'yyyy-MM-dd'))" }
Add-Content -Path $logFile -Value "$abs$comment"
"marked: $abs"

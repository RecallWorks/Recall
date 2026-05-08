# @recall.works/agent-os | latest-revival.ps1 | v1.0
# Print newest REVIVAL doc(s), qwen-compressed if older than 24h.
#
# Usage:
#   pwsh ./latest-revival.ps1                # newest, raw if <24h or qwen-compressed
#   pwsh ./latest-revival.ps1 -Topic sp -N 2 # 2 newest matching REVIVAL-S*-sp*.md
#   pwsh ./latest-revival.ps1 -Raw           # always raw

[CmdletBinding()]
param(
    [string] $Config = (Join-Path $PSScriptRoot '..\config.json'),
    [int]    $N = 1,
    [switch] $Raw,
    [string] $Topic = ''
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json

$revDir = Join-Path ([System.Environment]::ExpandEnvironmentVariables($cfg.workspace.primary)) 'REVIVAL'
if (-not (Test-Path $revDir)) { Write-Error "no revival dir at $revDir"; exit 3 }

$pattern = if ($Topic) { "REVIVAL-S*-$Topic*.md" } else { 'REVIVAL-S*.md' }
$docs = Get-ChildItem -Path $revDir -Filter $pattern |
    Where-Object { $_.Name -notmatch '\.compact\.md$' } |
    Sort-Object LastWriteTime -Descending | Select-Object -First $N
if (-not $docs) { Write-Error "no revival docs match $pattern"; exit 4 }

foreach ($doc in $docs) {
    $ageH = ((Get-Date) - $doc.LastWriteTime).TotalHours
    Write-Output "===== $($doc.Name) ===== ($([int]$ageH)h old, $([int]($doc.Length/1024))KB)"

    if ($Raw -or $ageH -lt 24) {
        Get-Content $doc.FullName -Raw
        continue
    }

    $cacheFile = Join-Path $revDir ("$($doc.BaseName).compact.md")
    $cacheValid = (Test-Path $cacheFile) -and ((Get-Item $cacheFile).LastWriteTime -gt $doc.LastWriteTime)

    if (-not $cacheValid) {
        $prompt = @'
You are compressing a session-recovery doc into telegraphese.
Output sections in order:
1. status: 1 line. CLOSED|OPEN|BLOCKED + 1-line state.
2. blockers: bullets of what's stuck + why.
3. next-action: 1-3 bullets, the next concrete step.
4. untested: bullets of what was NOT verified.
5. files: paths touched, comma-separated.
PRESERVE: file paths, hex sigs, identifiers, REVIVAL-* refs.
DROP: prose, articles, pronouns. Use → + : ; for connectors.
60 lines max total.
'@
        $body = Get-Content $doc.FullName -Raw
        $payload = @{
            model = $cfg.localModel.model
            prompt = "$prompt`n`n=== INPUT ===`n$body"
            stream = $false
            options = @{ temperature = 0.2; num_ctx = 16384 }
        } | ConvertTo-Json -Depth 5 -Compress

        try {
            $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 120
            $resp.response | Set-Content -Path $cacheFile -Encoding UTF8
        } catch {
            Write-Output "[qwen unavailable, raw fallback] $($_.Exception.Message)"
            Get-Content $doc.FullName -Raw
            continue
        }
    }
    Get-Content $cacheFile -Raw
}

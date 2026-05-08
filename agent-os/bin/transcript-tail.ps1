# @recall.works/agent-os | transcript-tail.ps1 | v1.0
# Locate the active editor's chat transcript (currently: GitHub Copilot Chat
# under VS Code) and emit the last N KB.
#
# Usage:  pwsh ./transcript-tail.ps1 [-Config ../config.json] [-TailKB 200] [-OutFile path]

[CmdletBinding()]
param(
    [string] $Config  = (Join-Path $PSScriptRoot '..\config.json'),
    [int]    $TailKB  = 200,
    [string] $OutFile = (Join-Path $env:TEMP 'transcript-tail.jsonl')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Config)) { Write-Error "config not found: $Config"; exit 2 }
$cfg = Get-Content $Config -Raw | ConvertFrom-Json
$tdir = [System.Environment]::ExpandEnvironmentVariables(
    $cfg.memory.transcriptsDir.Replace('<workspaceId>', $cfg.memory.workspaceId)
)
if (-not (Test-Path $tdir)) { Write-Error "transcripts dir not found: $tdir (set memory.workspaceId in config.json)"; exit 3 }

$active = Get-ChildItem $tdir -Filter *.jsonl |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $active) { Write-Error "no transcript files in $tdir"; exit 4 }

$bytes = $TailKB * 1KB
$startOffset = [Math]::Max(0, $active.Length - $bytes)

$fs = [System.IO.File]::OpenRead($active.FullName)
try {
    $fs.Seek($startOffset, 'Begin') | Out-Null
    $buf = New-Object byte[] ($active.Length - $startOffset)
    [void]$fs.Read($buf, 0, $buf.Length)
} finally { $fs.Dispose() }

$text = [System.Text.Encoding]::UTF8.GetString($buf)
if ($startOffset -gt 0) {
    $nl = $text.IndexOf("`n")
    if ($nl -ge 0) { $text = $text.Substring($nl + 1) }
}

[System.IO.File]::WriteAllText($OutFile, $text, [System.Text.UTF8Encoding]::new($false))

[pscustomobject]@{
    Transcript   = $active.Name
    SessionId    = [System.IO.Path]::GetFileNameWithoutExtension($active.Name)
    FullSizeKB   = [math]::Round($active.Length / 1KB, 1)
    TailKB       = [math]::Round($buf.Length   / 1KB, 1)
    OutFile      = $OutFile
    LastWriteUtc = $active.LastWriteTimeUtc
}

# one-shot: add social row to footer + bump brand stamps + JSON-LD sameAs
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$site = "D:\Dev\_scratch\recall-clone\site"

$socialRow = @'
    <div class="social"><strong>Follow:</strong>
      <a href="https://x.com/MtgtechUSA">X / Twitter</a> &middot;
      <a href="https://linkedin.com/company/mortgagetech">LinkedIn</a> &middot;
      <a href="https://youtube.com/@Mortgagetech8888172299">YouTube</a>
    </div>
'@

# bump map: file -> [oldStamp, newStamp]
$bumps = @{
  'architecture.html' = @('v1.3','v1.4')
  'brain.html'        = @('v1.5','v1.6')
  'comparison.html'   = @('v1.4','v1.5')
  'hardware.html'     = @('v1.4','v1.5')
  'index.html'        = @('v1.4','v1.5')
  'pillars.html'      = @('v1.4','v1.5')
  'quickstart.html'   = @('v1.3','v1.4')
  'whitepaper.html'   = @('v1.4','v1.5')
}

foreach ($name in $bumps.Keys) {
  $path = Join-Path $site $name
  $txt  = [IO.File]::ReadAllText($path)

  # 1) inject social row inside footer .meta div, before </div></footer>
  if ($txt -notmatch 'class="social"') {
    $txt = $txt -replace '(<div><strong>Site generated:[^<]*</strong>[^<]*</div>)', "`$1`r`n$socialRow"
  }

  # 2) bump brand stamp
  $old = $bumps[$name][0]; $new = $bumps[$name][1]
  $txt = [regex]::Replace(
    $txt,
    '<!-- @recall\.works/site \| (' + [regex]::Escape($name) + ') \| ' + [regex]::Escape($old) + ' \| 2026-05-08 \|[^|]*\| prev: [^-]+-->',
    "<!-- @recall.works/site | `$1 | $new | 2026-05-08 | added social links to footer (X/LinkedIn/YouTube) | prev: $old -->"
  )

  [IO.File]::WriteAllText($path, $txt, $utf8NoBom)
  Write-Host "ok: $name $old -> $new"
}

# 3) JSON-LD sameAs on index.html
$idx = Join-Path $site 'index.html'
$txt = [IO.File]::ReadAllText($idx)
if ($txt -notmatch '"sameAs"') {
  $txt = $txt -replace '("url": "https://github\.com/stevepaltridge")(\s*\})', '$1$2,
  "sameAs": [
    "https://x.com/MtgtechUSA",
    "https://linkedin.com/company/mortgagetech",
    "https://youtube.com/@Mortgagetech8888172299"
  ]'
  # the regex above is wrong placement; redo cleanly:
}
# Cleaner: insert sameAs as new top-level field after author block
$txt = [IO.File]::ReadAllText($idx)
if ($txt -notmatch '"sameAs"') {
  $txt = $txt -replace '("keywords": "AI agents[^"]*")', '"sameAs": [
    "https://x.com/MtgtechUSA",
    "https://linkedin.com/company/mortgagetech",
    "https://youtube.com/@Mortgagetech8888172299",
    "https://github.com/RecallWorks/Recall"
  ],
  $1'
  [IO.File]::WriteAllText($idx, $txt, $utf8NoBom)
  Write-Host "ok: index.html JSON-LD sameAs added"
}

# 4) update twitter:site casing (already @mtgtechusa, swap to @MtgtechUSA for display)
foreach ($name in $bumps.Keys) {
  $path = Join-Path $site $name
  $txt = [IO.File]::ReadAllText($path)
  if ($txt -match 'twitter:site" content="@mtgtechusa"') {
    $txt = $txt -replace '"@mtgtechusa"','"@MtgtechUSA"'
    [IO.File]::WriteAllText($path, $txt, $utf8NoBom)
  }
}

Write-Host "DONE"

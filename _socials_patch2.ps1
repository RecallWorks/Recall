$utf8 = New-Object System.Text.UTF8Encoding $false
$site = "D:\Dev\_scratch\recall-clone\site"

$socialRow = @'
    <div class="social"><strong>Follow:</strong>
      <a href="https://x.com/MtgtechUSA">X / Twitter</a> &middot;
      <a href="https://linkedin.com/company/mortgagetech">LinkedIn</a> &middot;
      <a href="https://youtube.com/@MortgageTechAI">YouTube</a>
    </div>
  </div>
</footer>
'@

# stamp bumps for the 6 footer-less files
$bumps = @{
  'architecture.html' = @('v1.4','v1.5')
  'brain.html'        = @('v1.6','v1.7')
  'comparison.html'   = @('v1.5','v1.6')
  'hardware.html'     = @('v1.5','v1.6')
  'pillars.html'      = @('v1.5','v1.6')
  'whitepaper.html'   = @('v1.5','v1.6')
}

foreach ($name in $bumps.Keys) {
  $path = Join-Path $site $name
  $txt  = [IO.File]::ReadAllText($path)

  if ($txt -match 'class="social"') { Write-Host "skip (already has social): $name"; continue }

  # inject social row by replacing the closing footer pattern
  $txt = [regex]::Replace($txt, '\s*</div>\s*</footer>', "`r`n$socialRow", 1)

  $old = $bumps[$name][0]; $new = $bumps[$name][1]
  $txt = [regex]::Replace(
    $txt,
    '<!-- @recall\.works/site \| (' + [regex]::Escape($name) + ') \| ' + [regex]::Escape($old) + ' \|[^>]*-->',
    "<!-- @recall.works/site | `$1 | $new | 2026-05-08 | added social links to footer (X/LinkedIn/YouTube @MortgageTechAI) | prev: $old -->"
  )

  [IO.File]::WriteAllText($path, $txt, $utf8)
  Write-Host "ok: $name $old -> $new"
}

Write-Host "DONE"

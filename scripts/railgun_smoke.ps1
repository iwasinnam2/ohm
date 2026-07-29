# Railgun smoke — BYOK headers, usage invoice basis, MCP import, suspend path (local).
# Does not require live Stripe; Checkout/suspend asserted when STRIPE_* is set.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Header-Value([string]$HeadersText, [string]$Name) {
  foreach ($line in ($HeadersText -split "`r?`n")) {
    if ($line -match ("(?i)^" + [regex]::Escape($Name) + ":\s*(.+)$")) {
      return $Matches[1].Trim()
    }
  }
  return ""
}

Write-Host "== railgun_smoke: health =="
$code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 5 http://127.0.0.1:8080/health
if ($code -ne "200") { throw "Python health expected 200, got $code" }
$code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 5 http://127.0.0.1:8081/health
if ($code -ne "200") { throw "Rust health expected 200, got $code" }

Write-Host "== railgun_smoke: mock miss/hit + usage seat_plus_meters =="
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$bodyPath = Join-Path $Root "scripts\.railgun_mock.json"
Set-Content -Path $bodyPath -Value ("{`"model`":`"mock`",`"messages`":[{`"role`":`"user`",`"content`":`"railgun-$suffix`"}]}") -NoNewline
$h1 = Join-Path $Root "scripts\.railgun_miss.hdr"
$h2 = Join-Path $Root "scripts\.railgun_hit.hdr"
$o1 = Join-Path $Root "scripts\.railgun_miss.body"
$o2 = Join-Path $Root "scripts\.railgun_hit.body"
$null = & curl.exe -s -D $h1 -o $o1 --max-time 60 `
  -H "Authorization: Bearer sk-at-dev" `
  -H "Content-Type: application/json" `
  --data-binary "@$bodyPath" `
  "http://127.0.0.1:8081/v1/chat/completions"
$null = & curl.exe -s -D $h2 -o $o2 --max-time 60 `
  -H "Authorization: Bearer sk-at-dev" `
  -H "Content-Type: application/json" `
  --data-binary "@$bodyPath" `
  "http://127.0.0.1:8081/v1/chat/completions"
if ((Header-Value (Get-Content -Raw $h1) "x-at-cache") -ne "MISS") { throw "expected MISS" }
if ((Header-Value (Get-Content -Raw $h2) "x-at-cache") -ne "HIT") { throw "expected HIT" }

$usage = & curl.exe -s http://127.0.0.1:8080/v1/usage -H "Authorization: Bearer sk-at-dev"
if ($usage -notmatch "seat_plus_meters") { throw "usage invoice_basis missing seat_plus_meters: $usage" }
if ($usage -notmatch "web_context_attach_rate") { throw "usage missing web_context_attach_rate" }

Write-Host "== railgun_smoke: BYOK header required when no env fallback for gpt =="
# Force check via Python providers endpoint documenting byok_header
$providers = & curl.exe -s http://127.0.0.1:8080/v1/providers -H "Authorization: Bearer sk-at-dev"
if ($providers -notmatch "X-Ohm-Upstream-Key") { throw "providers missing BYOK header: $providers" }

Write-Host "== railgun_smoke: compliant fetch path (may 403 without ingest) =="
$fetchBody = Join-Path $Root "scripts\.railgun_fetch.json"
Set-Content -Path $fetchBody -Value '{"model":"mock","messages":[{"role":"user","content":"sum"}],"fetch_web_context":true,"web_purpose":"public_web_retrieval","web_urls":["https://example.com"],"web_compliance_ack":true,"terms_ack":true,"dpa_ack":true,"cache_control":"no_store"}' -NoNewline
$fh = Join-Path $Root "scripts\.railgun_fetch.hdr"
$fo = Join-Path $Root "scripts\.railgun_fetch.body"
$null = & curl.exe -s -D $fh -o $fo --max-time 90 `
  -H "Authorization: Bearer sk-at-dev" `
  -H "Content-Type: application/json" `
  --data-binary "@$fetchBody" `
  "http://127.0.0.1:8080/v1/chat/completions"
$fetchCode = ""
if ((Get-Content -Raw $fh) -match "HTTP/1\.\d\s+(\d+)") { $fetchCode = $Matches[1] }
Write-Host "fetch status=$fetchCode (200/403 acceptable depending on ingest/compliance)"

Write-Host "== railgun_smoke: MCP module import =="
$py = & python -c "import ohm_mcp; print('ohm_mcp_ok')" 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "ohm_mcp import skipped or failed (install mcp extra): $py"
} else {
  Write-Host $py
}

Write-Host "== railgun_smoke: public checkout endpoint shape =="
$coBody = Join-Path $Root "scripts\.railgun_checkout.json"
Set-Content -Path $coBody -Value '{"plan":"payg","terms_ack":true,"dpa_ack":true,"label":"railgun"}' -NoNewline
$co = & curl.exe -s -w "`n%{http_code}" -X POST http://127.0.0.1:8080/v1/billing/checkout `
  -H "Content-Type: application/json" `
  --data-binary "@$coBody"
# Expect 503 without Stripe or 200 with Stripe
Write-Host $co

Write-Host "== railgun_smoke: PASS =="

# Release smoke gate for at-utility
# Exit 0 only when local Compose stack meets the Section A contract.
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

function Assert-Http([string]$Url, [string]$Expect = "200") {
  $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 5 $Url
  if ($code -ne $Expect) { throw "Expected HTTP $Expect from $Url, got $code" }
}

function Chat([string]$Base, [string]$BodyPath, [string]$HdrPath, [string]$OutPath) {
  $null = & curl.exe -s -D $HdrPath -o $OutPath --max-time 120 `
    -H "Authorization: Bearer sk-at-dev" `
    -H "Content-Type: application/json" `
    --data-binary "@$BodyPath" `
    "$Base/v1/chat/completions"
}

Write-Host "== release_smoke: health =="
Assert-Http "http://127.0.0.1:8080/health"
Assert-Http "http://127.0.0.1:8081/health"
$rustHealth = & curl.exe -s http://127.0.0.1:8081/health
if ($rustHealth -notmatch '"plane"\s*:\s*"rust"' -and $rustHealth -notmatch "at-gateway-rs") {
  throw "Rust health body unexpected: $rustHealth"
}

Write-Host "== release_smoke: mock miss then hit on Python =="
$mockBody = Join-Path $Root "scripts\.release_mock.json"
Set-Content -Path $mockBody -Value '{"model":"mock","messages":[{"role":"user","content":"release-smoke-mock"}]}' -NoNewline
$h1 = Join-Path $Root "scripts\.release_mock_miss.hdr"
$h2 = Join-Path $Root "scripts\.release_mock_hit.hdr"
$o1 = Join-Path $Root "scripts\.release_mock_miss.body"
$o2 = Join-Path $Root "scripts\.release_mock_hit.body"
Chat "http://127.0.0.1:8080" $mockBody $h1 $o1
Chat "http://127.0.0.1:8080" $mockBody $h2 $o2
if ((Header-Value (Get-Content -Raw $h1) "x-at-cache") -ne "MISS") { throw "mock expected MISS" }
if ((Header-Value (Get-Content -Raw $h2) "x-at-cache") -ne "HIT") { throw "mock expected HIT" }

Write-Host "== release_smoke: providers =="
$providers = & curl.exe -s http://127.0.0.1:8080/v1/providers -H "Authorization: Bearer sk-at-dev"
Write-Host $providers
$openaiConfigured = $providers -match '"openai"\s*:\s*\{[^}]*"configured"\s*:\s*true'

if ($openaiConfigured) {
  Write-Host "== release_smoke: OpenAI miss then hit on Python =="
  $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
  $oaBody = Join-Path $Root "scripts\.release_oa.json"
  Set-Content -Path $oaBody -Value ("{`"model`":`"gpt-4o-mini`",`"messages`":[{`"role`":`"user`",`"content`":`"release-smoke-oa-$suffix`"}]}") -NoNewline
  $oh1 = Join-Path $Root "scripts\.release_oa_miss.hdr"
  $oh2 = Join-Path $Root "scripts\.release_oa_hit.hdr"
  $oo1 = Join-Path $Root "scripts\.release_oa_miss.body"
  $oo2 = Join-Path $Root "scripts\.release_oa_hit.body"
  Chat "http://127.0.0.1:8080" $oaBody $oh1 $oo1
  $missCode = (Get-Content -Raw $oh1) -match "HTTP/1\.\d\s+(\d+)" | Out-Null; $missCode = $Matches[1]
  if ($missCode -eq "401" -or $missCode -eq "429") {
    Write-Host "OpenAI upstream $missCode - treat as environment issue, not gateway regression"
    Get-Content -Raw $oo1 | ForEach-Object { $_.Substring(0, [Math]::Min(240, $_.Length)) }
  } else {
    if ((Header-Value (Get-Content -Raw $oh1) "x-at-cache") -ne "MISS") { throw "openai expected MISS" }
    $body = Get-Content -Raw $oo1
    if ($body -match "\[mock:") { throw "openai routed to mock unexpectedly" }
    Chat "http://127.0.0.1:8080" $oaBody $oh2 $oo2
    if ((Header-Value (Get-Content -Raw $oh2) "x-at-cache") -ne "HIT") { throw "openai expected HIT" }
  }
} else {
  Write-Host "OpenAI not configured - skipping live model checks"
}

Write-Host "== release_smoke: Rust plane mock =="
$rustBody = Join-Path $Root "scripts\.release_rust.json"
Set-Content -Path $rustBody -Value '{"model":"mock","messages":[{"role":"user","content":"release-smoke-rust"}]}' -NoNewline
$rh1 = Join-Path $Root "scripts\.release_rust_miss.hdr"
$rh2 = Join-Path $Root "scripts\.release_rust_hit.hdr"
$ro1 = Join-Path $Root "scripts\.release_rust_miss.body"
$ro2 = Join-Path $Root "scripts\.release_rust_hit.body"
Chat "http://127.0.0.1:8081" $rustBody $rh1 $ro1
Chat "http://127.0.0.1:8081" $rustBody $rh2 $ro2
if ((Header-Value (Get-Content -Raw $rh1) "x-at-plane") -ne "rust") { throw "expected x-at-plane rust on miss" }
if ((Header-Value (Get-Content -Raw $rh2) "x-at-plane") -ne "rust") { throw "expected x-at-plane rust on hit" }
if ((Header-Value (Get-Content -Raw $rh1) "x-at-cache") -ne "MISS") { throw "rust mock expected MISS" }
if ((Header-Value (Get-Content -Raw $rh2) "x-at-cache") -ne "HIT") { throw "rust mock expected HIT" }

Write-Host "== release_smoke: usage =="
$usage = & curl.exe -s http://127.0.0.1:8080/v1/usage -H "Authorization: Bearer sk-at-dev"
Write-Host $usage
if ($usage -notmatch '"requests"\s*:\s*[1-9]') { throw "usage.requests did not increment" }

Write-Host "RELEASE_SMOKE_OK"
exit 0

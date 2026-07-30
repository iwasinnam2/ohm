#Requires -Version 5.1
<#
.SYNOPSIS
  Golden path - walks the exact route a Cursor marketplace reviewer takes and
  fails loudly if any public claim is not true in production.

  Public (no key):   www homepage copy, /subscriptions pricing, /status,
                     api.withohm.dev health (Rust plane).
  Keyed (-ApiKey or $env:OHM_API_KEY):
                     chat MISS -> cache HIT (mirrors MCP ohm_chat),
                     SSE streaming, compliant web fetch (mirrors ohm_fetch_web),
                     /v1/usage metering delta (HITs are billed).

  Claims-to-tests map: INSPECTION.md at the repo root.

.EXAMPLE
  .\scripts\golden_path.ps1                         # public surfaces only
.EXAMPLE
  .\scripts\golden_path.ps1 -ApiKey sk-at-...       # full reviewer path
#>
param(
  [string]$ApiKey = $env:OHM_API_KEY,
  [string]$SiteUrl = "https://www.withohm.dev",
  [string]$ApiUrl = "https://api.withohm.dev",
  [switch]$SkipWebFetch
)

$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -lt 6) {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}
$failures = @()
$unique = "golden-$(Get-Date -Format 'yyyyMMddHHmmss')-$([guid]::NewGuid().ToString('N').Substring(0,6))"

function Step([string]$Name, [scriptblock]$Body) {
  try {
    & $Body
    Write-Host "OK   $Name"
  } catch {
    Write-Host "FAIL $Name -- $($_.Exception.Message)"
    $script:failures += $Name
  }
}

function Get-Page([string]$Url) {
  return Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 60
}

# --- Public surfaces (what the reviewer sees first) ---

Step "homepage 200 + grounded hero copy" {
  $r = Get-Page $SiteUrl
  if ($r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
  foreach ($phrase in @("model switching", "prompt caching", "BYOK", "MCP")) {
    if ($r.Content -notmatch [regex]::Escape($phrase)) { throw "missing phrase '$phrase'" }
  }
}

Step "subscriptions 200 + published pricing" {
  $r = Get-Page "$SiteUrl/subscriptions"
  if ($r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
  foreach ($phrase in @("2,500", "29", "`$0")) {
    if ($r.Content -notmatch [regex]::Escape($phrase)) { throw "missing pricing '$phrase'" }
  }
}

Step "status page 200 (single-region truth)" {
  $r = Get-Page "$SiteUrl/status"
  if ($r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
  if ($r.Content -match "Global Accelerator") { throw "stale multi-region claim on status page" }
}

Step "api health (Rust plane)" {
  $h = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 60 -UseBasicParsing
  if ($h.ok -ne $true) { throw "health.ok != true" }
}

# --- Keyed reviewer path (MCP tool equivalents over the public API) ---

if (-not $ApiKey) {
  Write-Host "SKIP keyed steps (no -ApiKey / OHM_API_KEY) - public surfaces only."
} else {
  $headers = @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" }
  $usageBefore = $null

  Step "usage baseline (GET /v1/usage)" {
    $script:usageBefore = Invoke-RestMethod -Uri "$ApiUrl/v1/usage" -Headers $headers -UseBasicParsing -TimeoutSec 60
    if ($null -eq $script:usageBefore.requests) { throw "no requests field" }
  }

  Step "chat MISS then metered cache HIT (ohm_chat)" {
    $payload = @{ model = "mock"; messages = @(@{ role = "user"; content = $unique }) } | ConvertTo-Json -Compress
    $miss = Invoke-WebRequest -Uri "$ApiUrl/v1/chat/completions" -Method POST -Headers $headers -Body $payload -UseBasicParsing -TimeoutSec 90
    if ([string]$miss.Headers["x-at-cache"] -notmatch "MISS") { throw "expected MISS, got '$($miss.Headers["x-at-cache"])'" }
    $hit = Invoke-WebRequest -Uri "$ApiUrl/v1/chat/completions" -Method POST -Headers $headers -Body $payload -UseBasicParsing -TimeoutSec 90
    if ([string]$hit.Headers["x-at-cache"] -notmatch "HIT") { throw "expected HIT, got '$($hit.Headers["x-at-cache"])'" }
  }

  Step "SSE streaming pass-through" {
    $payload = @{ model = "mock"; stream = $true; messages = @(@{ role = "user"; content = "stream-$unique" }) } | ConvertTo-Json -Compress
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
      & curl.exe -sS --max-time 90 -o $tmp -H "Authorization: Bearer $ApiKey" -H "Content-Type: application/json" --data-binary $payload "$ApiUrl/v1/chat/completions"
      if ($LASTEXITCODE -ne 0) { throw "curl exit $LASTEXITCODE" }
      $body = [System.IO.File]::ReadAllText($tmp)
      if ($body -notmatch "data:") { throw "no SSE 'data:' frames in response" }
    } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
  }

  if (-not $SkipWebFetch) {
    Step "compliant web fetch (ohm_fetch_web)" {
      $payload = @{
        model             = "mock"
        messages          = @(@{ role = "user"; content = "Summarize the web context." })
        fetch_web_context = $true
        web_purpose       = "public_web_retrieval"
        web_urls          = @("https://example.com/")
        cache_control     = "no_store"
      } | ConvertTo-Json -Compress -Depth 6
      $r = Invoke-WebRequest -Uri "$ApiUrl/v1/chat/completions" -Method POST -Headers $headers -Body $payload -UseBasicParsing -TimeoutSec 120
      if ($r.StatusCode -ne 200) { throw "status $($r.StatusCode)" }
    }
  }

  Step "usage delta shows metered requests (ohm_usage)" {
    $after = Invoke-RestMethod -Uri "$ApiUrl/v1/usage" -Headers $headers -UseBasicParsing -TimeoutSec 60
    $delta = [int]$after.requests - [int]$script:usageBefore.requests
    if ($delta -lt 2) { throw "usage.requests grew by $delta (<2) - HITs may not be metered" }
  }
}

Write-Host ""
if ($failures.Count) {
  Write-Host "GOLDEN PATH FAILED: $($failures -join '; ')"
  exit 1
}
Write-Host "GOLDEN PATH PASSED ($SiteUrl / $ApiUrl)"

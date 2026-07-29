#Requires -Version 5.1
<#
.SYNOPSIS
  Production / external-network smoke against a public hostname (Section C exit criteria).
.EXAMPLE
  .\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-...
#>
param(
  [Parameter(Mandatory = $true)][string]$BaseUrl,
  [Parameter(Mandatory = $true)][string]$ApiKey,
  [string]$Model = "gpt-4o-mini",
  [switch]$SkipOpenAI
)

$ErrorActionPreference = "Stop"
$root = $BaseUrl.TrimEnd("/")
if (-not $root.EndsWith("/v1")) { $root = "$root/v1" }
$headers = @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" }
$unique = "ext-smoke-$(Get-Date -Format 'yyyyMMddHHmmss')"

function Assert-Ok($name, $cond, $detail = "") {
  if (-not $cond) { throw "FAIL: $name $detail" }
  Write-Host "OK: $name"
}

# Health is usually on host root, not under /v1
$healthRoot = $BaseUrl.TrimEnd("/")
if ($healthRoot.EndsWith("/v1")) { $healthRoot = $healthRoot.Substring(0, $healthRoot.Length - 3) }
$health = Invoke-RestMethod -Uri "$healthRoot/health" -Method GET
Assert-Ok "health" ($health.ok -eq $true)

$payload = @{ model = "mock"; messages = @(@{ role = "user"; content = $unique }) } | ConvertTo-Json -Compress
$miss = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $payload
$missCache = [string]$miss.Headers["x-at-cache"]
Assert-Ok "mock miss" ($missCache -match "MISS") ($missCache)
$hit = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $payload
$hitCache = [string]$hit.Headers["x-at-cache"]
Assert-Ok "mock hit" ($hitCache -match "HIT") ($hitCache)

if (-not $SkipOpenAI) {
  $op = "openai-$unique"
  $body = @{ model = $Model; messages = @(@{ role = "user"; content = $op }) } | ConvertTo-Json -Compress
  $om = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $body
  Assert-Ok "openai miss" ($om.StatusCode -eq 200)
  $oh = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $body
  Assert-Ok "openai hit" ($oh.Headers["x-at-cache"] -match "HIT")
}

$usage = Invoke-RestMethod -Uri "$root/usage" -Headers @{ Authorization = "Bearer $ApiKey" }
Assert-Ok "usage" ($usage.requests -ge 1)

Write-Host "External smoke passed against $BaseUrl"

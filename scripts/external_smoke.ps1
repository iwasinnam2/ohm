#Requires -Version 5.1
<#
.SYNOPSIS
  Production / external-network smoke against a public hostname (Section C exit criteria).
.EXAMPLE
  .\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-...
.EXAMPLE
  # Pre-DNS: TLS to NLB IP with api.withohm.dev SNI
  .\scripts\external_smoke.ps1 -BaseUrl https://api.withohm.dev -ApiKey sk-at-dev -SkipOpenAI -ResolveIp 1.2.3.4
#>
param(
  [Parameter(Mandatory = $true)][string]$BaseUrl,
  [Parameter(Mandatory = $true)][string]$ApiKey,
  [string]$Model = "gpt-4o-mini",
  [switch]$SkipOpenAI,
  # Optional: force TLS SNI to api host while connecting to NLB IP (pre-DNS cutover).
  [string]$ResolveIp = ""
)

$ErrorActionPreference = "Stop"
$root = $BaseUrl.TrimEnd("/")
if (-not $root.EndsWith("/v1")) { $root = "$root/v1" }
$unique = "ext-smoke-$(Get-Date -Format 'yyyyMMddHHmmss')"

function Assert-Ok($name, $cond, $detail = "") {
  if (-not $cond) { throw "FAIL: $name $detail" }
  Write-Host "OK: $name"
}

function Get-HeaderValue([string[]]$HeaderLines, [string]$Name) {
  # Multiple x-at-cache values possible (Rust edge + Python). Prefer HIT if any.
  $lines = @($HeaderLines | Where-Object { $_ -match ("(?i)^" + [regex]::Escape($Name) + ":") })
  if (-not $lines.Count) { return "" }
  $vals = @($lines | ForEach-Object { ($_ -split ":", 2)[1].Trim() })
  if ($vals -match "(?i)^HIT") { return ($vals | Where-Object { $_ -match "(?i)^HIT" } | Select-Object -First 1) }
  return $vals[-1]
}

function Invoke-CurlJson([string]$Method, [string]$Url, [string]$Body = $null) {
  $hdrFile = [System.IO.Path]::GetTempFileName()
  $bodyFile = [System.IO.Path]::GetTempFileName()
  $args = @("-sS", "-D", $hdrFile, "-o", $bodyFile, "-X", $Method, "--max-time", "90")
  if ($ResolveIp) {
    $uri = [Uri]$Url
    $port = if ($uri.Port -gt 0) { $uri.Port } elseif ($uri.Scheme -eq "https") { 443 } else { 80 }
    $args += @("--resolve", "$($uri.Host):${port}:$ResolveIp")
  }
  $args += @("-H", "Authorization: Bearer $ApiKey")
  if ($Body) {
    $payloadFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($payloadFile, $Body)
    $args += @("-H", "Content-Type: application/json", "--data-binary", "@$payloadFile")
  }
  $args += $Url
  & curl.exe @args
  if ($LASTEXITCODE -ne 0) { throw "curl failed ($LASTEXITCODE) for $Url" }
  $hdr = Get-Content $hdrFile
  $bodyText = [System.IO.File]::ReadAllText($bodyFile)
  Remove-Item $hdrFile, $bodyFile -ErrorAction SilentlyContinue
  if ($Body) { Remove-Item $payloadFile -ErrorAction SilentlyContinue }
  return @{ Headers = $hdr; Body = $bodyText; Cache = (Get-HeaderValue $hdr "x-at-cache") }
}

# Health is usually on host root, not under /v1
$healthRoot = $BaseUrl.TrimEnd("/")
if ($healthRoot.EndsWith("/v1")) { $healthRoot = $healthRoot.Substring(0, $healthRoot.Length - 3) }

if ($ResolveIp) {
  $healthResp = Invoke-CurlJson -Method GET -Url "$healthRoot/health"
  $health = $healthResp.Body | ConvertFrom-Json
} else {
  $health = Invoke-RestMethod -Uri "$healthRoot/health" -Method GET -UseBasicParsing
}
Assert-Ok "health" ($health.ok -eq $true)

$payload = @{ model = "mock"; messages = @(@{ role = "user"; content = $unique }) } | ConvertTo-Json -Compress

if ($ResolveIp) {
  $miss = Invoke-CurlJson -Method POST -Url "$root/chat/completions" -Body $payload
  Assert-Ok "mock miss" ($miss.Cache -match "MISS") ($miss.Cache)
  $hit = Invoke-CurlJson -Method POST -Url "$root/chat/completions" -Body $payload
  Assert-Ok "mock hit" ($hit.Cache -match "HIT") ($hit.Cache)
} else {
  $headers = @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" }
  $miss = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $payload -UseBasicParsing
  $missCache = [string]$miss.Headers["x-at-cache"]
  Assert-Ok "mock miss" ($missCache -match "MISS") ($missCache)
  $hit = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $payload -UseBasicParsing
  $hitCache = [string]$hit.Headers["x-at-cache"]
  Assert-Ok "mock hit" ($hitCache -match "HIT") ($hitCache)
}

if (-not $SkipOpenAI) {
  $op = "openai-$unique"
  $body = @{ model = $Model; messages = @(@{ role = "user"; content = $op }) } | ConvertTo-Json -Compress
  if ($ResolveIp) {
    $om = Invoke-CurlJson -Method POST -Url "$root/chat/completions" -Body $body
    Assert-Ok "openai miss" ($om.Body -match '"object"') ($om.Body.Substring(0, [Math]::Min(120, $om.Body.Length)))
    $oh = Invoke-CurlJson -Method POST -Url "$root/chat/completions" -Body $body
    Assert-Ok "openai hit" ($oh.Cache -match "HIT") ($oh.Cache)
  } else {
    $headers = @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" }
    $om = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $body -UseBasicParsing
    Assert-Ok "openai miss" ($om.StatusCode -eq 200)
    $oh = Invoke-WebRequest -Uri "$root/chat/completions" -Method POST -Headers $headers -Body $body -UseBasicParsing
    Assert-Ok "openai hit" ($oh.Headers["x-at-cache"] -match "HIT")
  }
}

if ($ResolveIp) {
  $usageResp = Invoke-CurlJson -Method GET -Url "$root/usage"
  $usage = $usageResp.Body | ConvertFrom-Json
} else {
  $usage = Invoke-RestMethod -Uri "$root/usage" -Headers @{ Authorization = "Bearer $ApiKey" } -UseBasicParsing
}
Assert-Ok "usage" ($usage.requests -ge 1)

Write-Host "External smoke passed against $BaseUrl"

#Requires -Version 5.1
<#
.SYNOPSIS
  Stripe checkout → cancel → expect chat 403 on the public API (post-DNS).
.EXAMPLE
  .\scripts\stripe_public_lifecycle.ps1 -BaseUrl https://api.withohm.dev -AdminKey $env:AT_ADMIN_API_KEY
#>
param(
  [Parameter(Mandatory = $true)][string]$BaseUrl,
  [Parameter(Mandatory = $true)][string]$AdminKey,
  [string]$Plan = "payg",
  [string]$ResolveIp = ""
)

$ErrorActionPreference = "Stop"
$root = $BaseUrl.TrimEnd("/")
if (-not $root.EndsWith("/v1")) { $root = "$root/v1" }

function Invoke-Api([string]$Method, [string]$Url, [hashtable]$Headers = @{}, [string]$Body = $null) {
  if ($ResolveIp) {
    $hdrFile = [System.IO.Path]::GetTempFileName()
    $bodyFile = [System.IO.Path]::GetTempFileName()
    $uri = [Uri]$Url
    $port = if ($uri.Port -gt 0) { $uri.Port } elseif ($uri.Scheme -eq "https") { 443 } else { 80 }
    $args = @("-sS", "-D", $hdrFile, "-o", $bodyFile, "-X", $Method, "--max-time", "90",
      "--resolve", "$($uri.Host):${port}:$ResolveIp")
    foreach ($k in $Headers.Keys) { $args += @("-H", "${k}: $($Headers[$k])") }
    if ($Body) {
      $pf = [System.IO.Path]::GetTempFileName()
      [System.IO.File]::WriteAllText($pf, $Body)
      $args += @("-H", "Content-Type: application/json", "--data-binary", "@$pf")
    }
    $args += $Url
    & curl.exe @args
    if ($LASTEXITCODE -ne 0) { throw "curl failed for $Url" }
    $text = [System.IO.File]::ReadAllText($bodyFile)
    $code = 0
    $statusLine = (Get-Content $hdrFile | Select-Object -First 1)
    if ($statusLine -match "HTTP/\S+\s+(\d+)") { $code = [int]$Matches[1] }
    Remove-Item $hdrFile, $bodyFile -ErrorAction SilentlyContinue
    if ($Body) { Remove-Item $pf -ErrorAction SilentlyContinue }
    return @{ StatusCode = $code; Body = $text }
  }
  $params = @{ Uri = $Url; Method = $Method; Headers = $Headers; UseBasicParsing = $true }
  if ($Body) { $params.Body = $Body; $params.ContentType = "application/json" }
  try {
    $r = Invoke-WebRequest @params
    return @{ StatusCode = [int]$r.StatusCode; Body = $r.Content }
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $text = $reader.ReadToEnd()
    return @{ StatusCode = [int]$resp.StatusCode; Body = $text }
  }
}

$adminHeaders = @{ Authorization = "Bearer $AdminKey" }
$label = "lifecycle-$(Get-Date -Format 'yyyyMMddHHmmss')"
$issueBody = @{ label = $label; plan = $Plan } | ConvertTo-Json -Compress
$issued = Invoke-Api POST "$root/admin/tenants" $adminHeaders $issueBody
if ($issued.StatusCode -notin 200, 201) { throw "issue tenant failed: $($issued.StatusCode) $($issued.Body)" }
$tenant = $issued.Body | ConvertFrom-Json
$tenantId = $tenant.tenant_id
$apiKey = $tenant.api_key
Write-Host "OK: issued tenant=$tenantId"

$checkoutBody = @{ plan = $Plan } | ConvertTo-Json -Compress
$checkout = Invoke-Api POST "$root/admin/tenants/$tenantId/checkout" $adminHeaders $checkoutBody
if ($checkout.StatusCode -ne 200) { throw "checkout failed: $($checkout.StatusCode) $($checkout.Body)" }
$session = ($checkout.Body | ConvertFrom-Json)
Write-Host "OK: checkout url=$($session.url)"
Write-Host "ACTION: complete Checkout with test card 4242..., then press Enter"
Read-Host | Out-Null

# Cancel via Stripe Dashboard or set status suspended via admin for abort path
$suspendBody = @{ status = "suspended" } | ConvertTo-Json -Compress
$sus = Invoke-Api POST "$root/admin/tenants/$tenantId/status" $adminHeaders $suspendBody
Write-Host "OK: admin suspend status=$($sus.StatusCode)"

$chatBody = @{ model = "mock"; messages = @(@{ role = "user"; content = "post-cancel" }) } | ConvertTo-Json -Compress
$chat = Invoke-Api POST "$root/chat/completions" @{ Authorization = "Bearer $apiKey" } $chatBody
if ($chat.StatusCode -ne 403) {
  throw "FAIL: expected 403 after suspend, got $($chat.StatusCode) $($chat.Body)"
}
Write-Host "OK: chat 403 after suspend"
Write-Host "Stripe public lifecycle (admin-suspend path) passed against $BaseUrl"
Write-Host "Note: full webhook path still requires DNS so Stripe can POST /v1/billing/webhook"

#Requires -Version 5.1
<#
.SYNOPSIS
  Measure Global Datastore lag: SET on leader primary, GET on edge secondary.
.EXAMPLE
  .\scripts\redis_global_lag_drill.ps1 -LeaderPrimaryHost master.xxx.use1.cache.amazonaws.com -EdgeGetHost master.xxx.usw2.cache.amazonaws.com -Tls
#>
param(
  [Parameter(Mandatory = $true)][string]$LeaderPrimaryHost,
  [Parameter(Mandatory = $true)][string]$EdgeGetHost,
  [int]$BudgetMs = 1000,
  [switch]$Tls,
  [string]$KeyPrefix = "ohm-lag-drill"
)

$ErrorActionPreference = "Stop"
$key = "$KeyPrefix-$(Get-Date -Format 'yyyyMMddHHmmss')"
$val = "v-$(Get-Random)"

function Invoke-RedisCli {
  param([string]$Host, [string[]]$Args, [switch]$UseTls)
  $scheme = if ($UseTls) { "rediss" } else { "redis" }
  $uri = "${scheme}://${Host}:6379/0"
  # Requires redis-cli in PATH (or docker run redis:7-alpine redis-cli ...)
  $all = @("-u", $uri) + $Args
  $out = & redis-cli @all 2>&1
  if ($LASTEXITCODE -ne 0) { throw "redis-cli failed: $out" }
  return ($out | Out-String).Trim()
}

Write-Host "SET on leader $LeaderPrimaryHost"
Invoke-RedisCli -Host $LeaderPrimaryHost -UseTls:$Tls -Args @("SET", $key, $val, "EX", "120") | Out-Null

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$deadline = [DateTime]::UtcNow.AddMilliseconds($BudgetMs)
$hit = $false
while ([DateTime]::UtcNow -lt $deadline) {
  $got = Invoke-RedisCli -Host $EdgeGetHost -UseTls:$Tls -Args @("GET", $key)
  if ($got -eq $val) {
    $hit = $true
    break
  }
  Start-Sleep -Milliseconds 50
}
$sw.Stop()

if (-not $hit) {
  Write-Host "FAIL: no edge GET within ${BudgetMs}ms (last=$got)"
  exit 1
}

Write-Host "PASS: edge GET matched in $($sw.ElapsedMilliseconds)ms (budget ${BudgetMs}ms)"
exit 0

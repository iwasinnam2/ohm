#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy Ohm gateway stack to an edge EKS cluster using terraform edge_wiring.
.EXAMPLE
  .\infra\scripts\edge_k8s_deploy.ps1 -Region us-west-2
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet("us-west-2", "eu-west-2")][string]$Region,
  [string]$GatewayImageTag = "0.1.2",
  [string]$GatewayRsImageTag = "0.1.5",
  [string]$IngestImageTag = "0.1.1"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$TfDir = Join-Path $Root "infra/terraform"
$Ns = "at-utility"
$Account = "594161136574"
$Ecr = "$Account.dkr.ecr.us-east-1.amazonaws.com"

Push-Location $TfDir
$wiring = terraform output -json edge_wiring | ConvertFrom-Json
Pop-Location
if (-not $wiring.$Region) { throw "No edge_wiring for $Region - enable_edges and apply first" }

$w = $wiring.$Region

$cluster = $w.eks_cluster_name
$acm = $w.acm_certificate_arn
Write-Host "Region=$Region cluster=$cluster"

aws eks update-kubeconfig --region $Region --name $cluster --alias "ohm-$Region" | Out-Null
kubectl config use-context "ohm-$Region" | Out-Null

$prevEa = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$nsExists = kubectl get ns $Ns -o name 2>$null
$ErrorActionPreference = $prevEa
if (-not $nsExists) { kubectl create namespace $Ns | Out-Null }

# Copy bootstrap keys from leader context if available; otherwise require env / .env.
$leaderKeys = @{}
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
      $k = $Matches[1]; $v = $Matches[2].Trim().Trim('"').Trim("'")
      if ($v -and -not $leaderKeys.ContainsKey($k)) { $leaderKeys[$k] = $v }
    }
  }
}
try {
  $contexts = @(kubectl config get-contexts -o name)
  $leaderCtx = $contexts | Where-Object { $_ -eq "ohm-us-east-1" -or $_ -match "at-utility-eks" } | Select-Object -First 1
  if ($leaderCtx) {
    kubectl config use-context $leaderCtx | Out-Null
    $prevEa = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $rawJson = kubectl -n $Ns get secret at-utility-secrets -o json 2>$null
    $ErrorActionPreference = $prevEa
    if ($rawJson) {
      $raw = $rawJson | ConvertFrom-Json
      foreach ($k in $raw.data.PSObject.Properties.Name) {
        $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($raw.data.$k))
        if ($decoded) { $leaderKeys[$k] = $decoded }
      }
      Write-Host "Loaded non-empty keys from leader secret"
    }
  }
} finally {
  kubectl config use-context "ohm-$Region" | Out-Null
}

function Need([string]$Name, [string]$Fallback = "") {
  if ($leaderKeys.ContainsKey($Name) -and $leaderKeys[$Name]) { return $leaderKeys[$Name] }
  $envVal = [Environment]::GetEnvironmentVariable($Name)
  if ($envVal) { return $envVal }
  if ($Fallback) { return $Fallback }
  throw "Missing secret $Name (copy from leader or set env)"
}

# Phase 4: Rust RESP is plain TCP; fail-fast Redis so edge proxies to Python for cache/auth.
$literals = @{
  AT_API_KEYS           = (Need "AT_API_KEYS" "sk-at-dev")
  AT_ADMIN_API_KEYS     = (Need "AT_ADMIN_API_KEYS" (Need "AT_API_KEYS" "sk-at-dev"))
  OPENAI_API_KEY        = (Need "OPENAI_API_KEY")
  STRIPE_WEBHOOK_SECRET = (Need "STRIPE_WEBHOOK_SECRET" "")
  REDIS_URL             = [string]$w.REDIS_URL
  REDIS_WRITE_URL       = [string]$w.REDIS_WRITE_URL
  REDIS_RL_URL          = [string]$w.REDIS_RL_URL
  AT_RS_REDIS           = "127.0.0.1:9"
  AT_RS_REDIS_WRITE     = "127.0.0.1:9"
}

$args = @("-n", $Ns, "create", "secret", "generic", "at-utility-secrets", "--dry-run=client", "-o", "yaml")
foreach ($k in $literals.Keys) {
  if ($literals[$k]) { $args += "--from-literal=$k=$($literals[$k])" }
}
$yaml = & kubectl @args
$yaml | kubectl apply -f -

# Patch manifests: ACM + region + images
$manifest = Get-Content (Join-Path $Root "infra/k8s/manifests.yaml") -Raw
$manifest = $manifest.Replace("ACM_CERTIFICATE_ARN_PLACEHOLDER", $acm)
$manifest = $manifest.Replace('AT_REGION: "us-east-1"', "AT_REGION: `"$Region`"")
$manifest = $manifest -replace "at-utility/gateway:[0-9.]+", "at-utility/gateway:$GatewayImageTag"
$manifest = $manifest -replace "at-utility/gateway-rs:[0-9.]+", "at-utility/gateway-rs:$GatewayRsImageTag"
$manifest = $manifest -replace "at-utility/ingest-worker:[0-9.]+", "at-utility/ingest-worker:$IngestImageTag"
$tmp = Join-Path $env:TEMP "ohm-edge-$Region.yaml"
Set-Content -Path $tmp -Value $manifest -Encoding utf8
kubectl apply -f $tmp

kubectl -n $Ns rollout status deploy/gateway --timeout=300s
kubectl -n $Ns rollout status deploy/gateway-rs --timeout=300s

$hostName = $null
for ($i = 0; $i -lt 60; $i++) {
  $hostName = kubectl -n $Ns get svc gateway-rs -o jsonpath="{.status.loadBalancer.ingress[0].hostname}"
  if ($hostName) { break }
  Start-Sleep -Seconds 5
}
if (-not $hostName) { throw "NLB hostname not ready in $Region" }
Write-Host "NLB_HOSTNAME_$($Region.ToUpper().Replace('-','_'))=$hostName"

$arn = aws elbv2 describe-load-balancers --region $Region --query "LoadBalancers[?DNSName=='$hostName'].LoadBalancerArn" --output text
Write-Host "NLB_ARN_$($Region.ToUpper().Replace('-','_'))=$arn"

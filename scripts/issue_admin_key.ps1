# Mint or revoke a withOhm admin API key with no chat / shell-history exposure.
#
#   Issue:   powershell -File scripts/issue_admin_key.ps1
#   Revoke:  powershell -File scripts/issue_admin_key.ps1 -Revoke
#
# An admin key is not issued by anything: Settings.is_admin_api_key does a plain
# set-membership test against the comma-separated AT_ADMIN_API_KEYS. Minting one
# is therefore generate -> append -> roll -> verify, which is what this does.
#
# Two things it protects you from.
#
# admin_api_key_set resolves `at_admin_api_keys or at_api_keys`, so while
# AT_ADMIN_API_KEYS is empty every AT_API_KEYS value is admin-capable by
# fallback. Writing a lone new key into that field would silently revoke all of
# them, so the script seeds the list with the fallback values and says so.
#
# It also refuses to leave the list empty, which would hand admin rights back to
# every tenant key at once.
#
# The key reaches your screen exactly once, at the end, for pasting into
# Cursor Dashboard -> Cloud Agents -> Secrets as OHM_ADMIN_KEY.

[CmdletBinding()]
param(
    [switch]$Revoke,
    [string]$Prefix = "sk-at-obs-",
    [string]$Namespace = "at-utility",
    [string]$SecretName = "at-utility-secrets",
    [string]$ApiBase = "https://api.withohm.dev"
)

$ErrorActionPreference = "Stop"

# Args go in as one array: passing them loosely lets PowerShell bind -n and -o
# to its own common parameters instead of handing them to kubectl.
function Invoke-Kubectl {
    param([Parameter(Mandatory = $true)][string[]]$KubectlArgs)
    $out = & kubectl @KubectlArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl $($KubectlArgs -join ' ') failed: $out"
    }
    return $out
}

function ConvertFrom-SecretField {
    param($Data, [string]$Field)
    $b64 = $Data.$Field
    if ([string]::IsNullOrWhiteSpace($b64)) { return "" }
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64))
}

function Split-KeyList {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return @() }
    return @($Raw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Set-AdminKeyList {
    param([string[]]$Keys)
    if (-not $Keys -or $Keys.Count -eq 0) {
        throw "Refusing to write an empty AT_ADMIN_API_KEYS: that would make every AT_API_KEYS value admin by fallback."
    }
    $joined = (@($Keys) -join ',')
    # A single-element array unrolls to a string, so a caller that used + would
    # have concatenated two keys into one. Round-trip the join to catch that.
    if (@($joined -split ',').Count -ne @($Keys).Count) {
        throw "Key list did not round-trip through the join; refusing to write a malformed AT_ADMIN_API_KEYS."
    }
    $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($joined))
    $patch = @{ data = @{ AT_ADMIN_API_KEYS = $b64 } } | ConvertTo-Json -Compress
    $tmp = New-TemporaryFile
    try {
        Set-Content -Path $tmp -Value $patch -Encoding ascii
        Invoke-Kubectl @('-n', $Namespace, 'patch', 'secret', $SecretName, '--type', 'merge', '--patch-file', "$tmp") | Out-Null
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

function Get-AdminOpsStatus {
    param([string]$Key)
    try {
        $res = Invoke-WebRequest -Uri "$ApiBase/v1/admin/ops" `
            -Headers @{ Authorization = "Bearer $Key" } `
            -UseBasicParsing -TimeoutSec 20
        return [int]$res.StatusCode
    } catch {
        $response = $_.Exception.Response
        if ($response -and $response.StatusCode) { return [int]$response.StatusCode }
        throw
    }
}

function Wait-ForStatus {
    param([string]$Key, [int]$Expected, [int]$Attempts = 10)
    for ($i = 1; $i -le $Attempts; $i++) {
        $status = Get-AdminOpsStatus -Key $Key
        if ($status -eq $Expected) { return $true }
        Write-Host "  attempt $i/$Attempts - /v1/admin/ops returned $status, waiting for $Expected..."
        Start-Sleep -Seconds 6
    }
    return $false
}

function Get-NewKey {
    # AT_ADMIN_API_KEYS is comma-separated and both planes trim each entry, so a
    # comma would split the key in two and surrounding space would vanish
    # silently. The generated tail is url-safe base64 and can contain neither.
    if ($Prefix -match ',') { throw "Prefix must not contain a comma: AT_ADMIN_API_KEYS is a comma-separated list." }
    if ($Prefix -ne $Prefix.Trim()) { throw "Prefix must not start or end with whitespace: both planes trim it away." }
    $bytes = New-Object 'System.Byte[]' 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    return $Prefix + $token
}

# --- read current state -----------------------------------------------------

$secretJson = (Invoke-Kubectl @('-n', $Namespace, 'get', 'secret', $SecretName, '-o', 'json')) -join "`n"
$data = ($secretJson | ConvertFrom-Json).data

$adminRaw = ConvertFrom-SecretField -Data $data -Field 'AT_ADMIN_API_KEYS'
$keys = @(Split-KeyList -Raw $adminRaw)

if ($keys.Count -eq 0) {
    $fallback = @(Split-KeyList -Raw (ConvertFrom-SecretField -Data $data -Field 'AT_API_KEYS'))
    if ($fallback.Count -eq 0) {
        throw "Neither AT_ADMIN_API_KEYS nor AT_API_KEYS is set on $SecretName; refusing to guess."
    }
    Write-Warning ("AT_ADMIN_API_KEYS is empty, so all {0} AT_API_KEYS value(s) are admin by fallback. " -f $fallback.Count +
        "Seeding the list with them so none of them lose access.")
    $keys = $fallback
}

Write-Host "Current admin key count: $($keys.Count)"

# --- revoke -----------------------------------------------------------------

if ($Revoke) {
    $secure = Read-Host -Prompt "Admin key to revoke (input hidden)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($secure)
    $target = [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
    [Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($ptr)

    if ($keys -notcontains $target) { throw "That key is not in AT_ADMIN_API_KEYS; nothing to revoke." }
    $remaining = @($keys | Where-Object { $_ -ne $target })
    if ($remaining.Count -eq 0) { throw "That is the last admin key; revoking it would fall back to AT_API_KEYS. Issue a replacement first." }

    Set-AdminKeyList -Keys $remaining
    Write-Host "Patched. Admin key count is now $($remaining.Count). Rolling gateway..."
    Invoke-Kubectl @('-n', $Namespace, 'rollout', 'restart', 'deploy/gateway', 'deploy/gateway-rs') | Out-Null
    Invoke-Kubectl @('-n', $Namespace, 'rollout', 'status', 'deploy/gateway', '--timeout=180s') | Out-Null
    Invoke-Kubectl @('-n', $Namespace, 'rollout', 'status', 'deploy/gateway-rs', '--timeout=180s') | Out-Null

    if (Wait-ForStatus -Key $target -Expected 403) {
        Write-Host "Revoked - /v1/admin/ops now rejects that key."
    } else {
        throw "Key still accepted after the rollout; investigate before assuming it is revoked."
    }
    $target = $null
    return
}

# --- issue ------------------------------------------------------------------

$newKey = Get-NewKey
Set-AdminKeyList -Keys (@($keys) + $newKey)
Write-Host "Patched. Admin key count is now $($keys.Count + 1). Rolling gateway..."

# Both planes need the new key. The Python control plane serves /v1/admin/* and
# authorizes with admin_dep; the Rust edge reads AT_ADMIN_API_KEYS purely so it
# stops denying admin keys with a 401 before Python ever sees them.
Invoke-Kubectl @('-n', $Namespace, 'rollout', 'restart', 'deploy/gateway', 'deploy/gateway-rs') | Out-Null
Invoke-Kubectl @('-n', $Namespace, 'rollout', 'status', 'deploy/gateway', '--timeout=180s') | Out-Null
Invoke-Kubectl @('-n', $Namespace, 'rollout', 'status', 'deploy/gateway-rs', '--timeout=180s') | Out-Null

if (-not (Wait-ForStatus -Key $newKey -Expected 200)) {
    throw ("Key was patched but /v1/admin/ops never accepted it. A 403 means the Python " +
        "control plane has not picked up the secret; a 401 means the Rust edge is still " +
        "denying the key before Python sees it, which also happens if the edge is running " +
        "a build from before it read AT_ADMIN_API_KEYS.")
}

Write-Host ""
Write-Host "Verified against $ApiBase/v1/admin/ops. Copy this into Cursor Dashboard ->"
Write-Host "Cloud Agents -> Secrets as OHM_ADMIN_KEY. It will not be shown again:"
Write-Host ""
Write-Host "    $newKey"
Write-Host ""
Write-Host "Then close this window, and run scripts/daily_upkeep.py once to confirm the"
Write-Host "sweep reports an 'admin ops' line instead of a SKIP."
$newKey = $null

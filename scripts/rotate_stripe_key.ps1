# Rotate the live Stripe secret key with zero chat / shell-history exposure.
#
#   1. Roll the key in the dashboard: dashboard.stripe.com/apikeys -> Roll key
#      (pick an expiry for the old key; the cluster keeps working on the old
#      key until this script patches the new one in).
#   2. Run:  powershell -File scripts/rotate_stripe_key.ps1
#      and paste the new key at the hidden prompt.
#
# The script verifies the key against Stripe before touching the cluster,
# patches only STRIPE_SECRET_KEY (webhook signing secret is unaffected by a
# key roll), restarts the API, and smoke-tests public checkout end to end.

$ErrorActionPreference = "Stop"

$secure = Read-Host -Prompt "New sk_live key (input hidden)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($secure)
$key = [Runtime.InteropServices.Marshal]::PtrToStringUni($ptr)
[Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($ptr)

if ($key -notmatch "^sk_live_") { throw "That is not an sk_live key; aborting." }

# Prove the key works before we swap it in (header auth: never on a command line).
$acct = Invoke-RestMethod -Uri "https://api.stripe.com/v1/account" `
    -Headers @{ Authorization = "Bearer $key" }
if (-not $acct.id) { throw "Stripe rejected the key; aborting." }
Write-Host "Key verified for account $($acct.id)."

$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($key))
$key = $null
$patch = @{ data = @{ STRIPE_SECRET_KEY = $b64 } } | ConvertTo-Json -Compress
$tmp = New-TemporaryFile
try {
    Set-Content -Path $tmp -Value $patch -Encoding ascii
    kubectl -n at-utility patch secret at-utility-secrets --type merge --patch-file $tmp
} finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
}

kubectl -n at-utility rollout restart deploy/gateway deploy/ingest-worker
kubectl -n at-utility rollout status deploy/gateway --timeout=180s
kubectl -n at-utility rollout status deploy/ingest-worker --timeout=120s

# End-to-end proof: public checkout must still mint a live Stripe session.
$body = '{"plan":"payg","label":"key-rotation smoke","terms_ack":true,"dpa_ack":true}'
$res = Invoke-RestMethod -Method Post `
    -Uri "https://api.withohm.dev/v1/billing/checkout" `
    -ContentType "application/json" -Body $body
if ($res.checkout.id -like "cs_live_*") {
    Write-Host "Rotation complete - live checkout verified ($($res.checkout.id.Substring(0, 20))...)."
} else {
    throw "Checkout smoke failed after rotation - investigate before expiring the old key."
}

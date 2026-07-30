# Verify apex withohm.dev cutover (Ops 1)
# Expect: www 200; apex either 301→www or serves Amplify (not Vercel 404 / NXDOMAIN forever).

$ErrorActionPreference = "Continue"
Write-Host "DNS apex A:"
Resolve-DnsName withohm.dev -Type A -ErrorAction SilentlyContinue | Format-Table -AutoSize
Write-Host "DNS www CNAME:"
Resolve-DnsName www.withohm.dev -Type CNAME -ErrorAction SilentlyContinue | Format-Table -AutoSize

function Probe($url) {
  try {
    $r = curl.exe -sSI --max-redirs 0 $url 2>&1
    Write-Host "---- $url"
    $r | Select-Object -First 12
  } catch {
    Write-Host "---- $url FAIL: $_"
  }
}

Probe "https://www.withohm.dev/i"
Probe "https://withohm.dev/i"
Probe "https://withohm.dev/"

Write-Host ""
Write-Host "Done when apex redirects (Location: https://www.withohm.dev/...) or returns 200 Amplify HTML."
Write-Host "If NXDOMAIN: set GoDaddy Domain Forward withohm.dev -> https://www.withohm.dev (301)."

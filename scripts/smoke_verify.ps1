# Smoke: MemoryStore Python + RESP stub for Rust cache (MISS -> HIT via Rust)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RedisPort = 16379
$PyPort = 18080
$RsPort = 18081

$env:PATH = "$env:USERPROFILE\.cargo\bin;" + $env:PATH
$exe = Join-Path $Root "gateway-rs\target\release\at-gateway-rs.exe"
if (-not (Test-Path $exe)) {
  throw "Missing release binary. Run: cargo build --release in gateway-rs"
}

function Stop-Proc([System.Diagnostics.Process]$p) {
  if ($null -ne $p -and -not $p.HasExited) {
    try { cmd /c "taskkill /PID $($p.Id) /T /F" | Out-Null } catch {}
  }
}

function Wait-Http([string]$Url, [int]$Tries = 50) {
  for ($i = 0; $i -lt $Tries; $i++) {
    try {
      $out = & curl.exe -s -o NUL -w "%{http_code}" --max-time 2 $Url 2>$null
      if ($out -eq "200") { return }
    } catch {}
    Start-Sleep -Milliseconds 400
  }
  throw "Timeout waiting for $Url"
}

function Header-Value([string]$HeadersText, [string]$Name) {
  foreach ($line in ($HeadersText -split "`r?`n")) {
    if ($line -match ("(?i)^" + [regex]::Escape($Name) + ":\s*(.+)$")) {
      return $Matches[1].Trim()
    }
  }
  return ""
}

$stub = $null
$py = $null
$rs = $null
try {
  Write-Host "== starting RESP stub on $RedisPort (Rust cache only) =="
  $stub = Start-Process -FilePath "python" `
    -ArgumentList @("scripts/resp_stub.py", "--port", "$RedisPort") `
    -WorkingDirectory $Root -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Root "scripts\.stub.out") `
    -RedirectStandardError (Join-Path $Root "scripts\.stub.err")
  Start-Sleep -Seconds 1
  if ($stub.HasExited) { throw "RESP stub exited early. See scripts/.stub.err" }

  Write-Host "== starting Python gateway on $PyPort (in-memory store) =="
  # Point at a closed port so gateway falls back to MemoryStore
  $pyCmd = @"
Set-Location '$Root'
`$env:REDIS_URL='redis://127.0.0.1:1/0'
`$env:AT_API_KEYS='sk-at-dev'
`$env:AT_REGION='local'
`$env:INGEST_WORKER_URL='http://127.0.0.1:8090'
python -m uvicorn at_utility.main:app --host 127.0.0.1 --port $PyPort
"@
  $py = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile","-Command",$pyCmd) `
    -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Root "scripts\.py.out") `
    -RedirectStandardError (Join-Path $Root "scripts\.py.err")
  Wait-Http "http://127.0.0.1:$PyPort/health"

  Write-Host "== starting Rust gateway on $RsPort =="
  $rsCmd = @"
`$env:AT_RS_LISTEN='127.0.0.1:$RsPort'
`$env:AT_RS_REDIS='127.0.0.1:$RedisPort'
`$env:AT_RS_PRIMARY='http://127.0.0.1:$PyPort'
`$env:AT_RS_FALLBACK='http://127.0.0.1:$PyPort'
`$env:AT_API_KEYS='sk-at-dev'
& '$exe'
"@
  $rs = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile","-Command",$rsCmd) `
    -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Root "scripts\.rs.out") `
    -RedirectStandardError (Join-Path $Root "scripts\.rs.err")
  Wait-Http "http://127.0.0.1:$RsPort/health"

  Write-Host "== health =="
  $health = & curl.exe -s "http://127.0.0.1:$RsPort/health"
  Write-Host $health
  if ($health -notmatch "at-gateway-rs") { throw "unexpected health body: $health" }

  $bodyFile = Join-Path $Root "scripts\.smoke_body.json"
  Set-Content -Path $bodyFile -Value '{"model":"mock","messages":[{"role":"user","content":"rust-front-smoke"}]}' -NoNewline

  Write-Host "== chat MISS via Rust :$RsPort =="
  $hdrFile = Join-Path $Root "scripts\.smoke_miss.hdr"
  $missBody = & curl.exe -s -D $hdrFile -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" --data-binary "@$bodyFile" "http://127.0.0.1:$RsPort/v1/chat/completions"
  $hdrs = Get-Content -Raw $hdrFile
  $missCache = Header-Value $hdrs "x-at-cache"
  $missPlane = Header-Value $hdrs "x-at-plane"
  Write-Host "x-at-cache=$missCache x-at-plane=$missPlane"
  Write-Host ("body=" + $missBody.Substring(0, [Math]::Min(200, $missBody.Length)))
  if ($missPlane -ne "rust") { throw "expected x-at-plane rust, got $missPlane" }
  if ($missCache -ne "MISS") { throw "expected MISS, got $missCache" }
  if ($missBody -notmatch "chat.completion|choices") { throw "bad MISS body: $missBody" }

  Write-Host "== chat HIT via Rust :$RsPort (RESP cache) =="
  $hdrFile2 = Join-Path $Root "scripts\.smoke_hit.hdr"
  $hitBody = & curl.exe -s -D $hdrFile2 -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" --data-binary "@$bodyFile" "http://127.0.0.1:$RsPort/v1/chat/completions"
  $hdrs2 = Get-Content -Raw $hdrFile2
  $hitCache = Header-Value $hdrs2 "x-at-cache"
  $hitPlane = Header-Value $hdrs2 "x-at-plane"
  Write-Host "x-at-cache=$hitCache x-at-plane=$hitPlane"
  if ($hitPlane -ne "rust") { throw "expected x-at-plane rust on HIT" }
  if ($hitCache -ne "HIT") { throw "expected HIT, got $hitCache body=$hitBody" }

  Write-Host "== Python direct MISS/HIT on :$PyPort (MemoryStore) =="
  $bodyFile2 = Join-Path $Root "scripts\.smoke_body2.json"
  Set-Content -Path $bodyFile2 -Value '{"model":"mock","messages":[{"role":"user","content":"py-stack-smoke"}]}' -NoNewline
  $h1 = Join-Path $Root "scripts\.py_miss.hdr"
  $h2 = Join-Path $Root "scripts\.py_hit.hdr"
  $null = & curl.exe -s -D $h1 -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" --data-binary "@$bodyFile2" "http://127.0.0.1:$PyPort/v1/chat/completions"
  $null = & curl.exe -s -D $h2 -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" --data-binary "@$bodyFile2" "http://127.0.0.1:$PyPort/v1/chat/completions"
  $pyMiss = Header-Value (Get-Content -Raw $h1) "x-at-cache"
  $pyHit = Header-Value (Get-Content -Raw $h2) "x-at-cache"
  Write-Host "py miss=$pyMiss hit=$pyHit"
  if ($pyMiss -ne "MISS") { throw "Python MISS failed: $pyMiss" }
  if ($pyHit -ne "HIT") { throw "Python HIT failed: $pyHit" }

  Write-Host "SMOKE_OK rust_entry=:$RsPort plane=rust cache=MISS->HIT"
  exit 0
}
finally {
  Stop-Proc $rs
  Stop-Proc $py
  Stop-Proc $stub
}

# Redis primary → replica lag smoke (Phase 1).
# Requires Docker Compose redis + redis-replica.
# Budget: SET on primary visible on replica within 1000ms (lab).

param(
    [int]$BudgetMs = 1000
)

$ErrorActionPreference = "Stop"

$key = "at:smoke:replica:lag:$([guid]::NewGuid().ToString('N').Substring(0,12))"
$val = "v-$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"

Write-Host "Starting redis + redis-replica…"
docker compose up -d redis redis-replica | Out-Null
Start-Sleep -Seconds 3

Write-Host "SET on primary key=$key"
$setOut = docker compose exec -T redis redis-cli SET $key $val EX 60
if ($setOut.Trim() -ne "OK") { throw "SET failed: $setOut" }

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$found = $null
while ($sw.ElapsedMilliseconds -lt $BudgetMs) {
    $found = (docker compose exec -T redis-replica redis-cli GET $key).Trim()
    if ($found -eq $val) { break }
    Start-Sleep -Milliseconds 25
}
$sw.Stop()

docker compose exec -T redis redis-cli DEL $key | Out-Null

if ($found -ne $val) {
    Write-Error "FAIL: replica did not observe SET within ${BudgetMs}ms (last='$found')"
    exit 1
}

Write-Host "PASS: replica lag $($sw.ElapsedMilliseconds)ms (budget ${BudgetMs}ms)"
exit 0

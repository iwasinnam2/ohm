# Local / Docker smoke verification for at-utility

## Prerequisites

- Release binary: `gateway-rs/target/release/at-gateway-rs.exe`
- Python package installed: `pip install -e ".[dev]"`
- Either **Docker Desktop** (`docker compose up --build`) **or** the local RESP stub below

## A. Docker Compose (when Docker is available)

```powershell
cd c:\Users\markk\OneDrive\Documents\at-utility
docker compose up --build -d
# Phase 1: primary→replica lag budget
.\scripts\redis_replica_smoke.ps1
# wait for healthy
curl http://localhost:8080/health
# MISS then HIT
curl -i http://localhost:8080/v1/chat/completions -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" -d "{\"model\":\"mock\",\"messages\":[{\"role\":\"user\",\"content\":\"smoke-cache\"}]}"
curl -i http://localhost:8080/v1/chat/completions -H "Authorization: Bearer sk-at-dev" -H "Content-Type: application/json" -d "{\"model\":\"mock\",\"messages\":[{\"role\":\"user\",\"content\":\"smoke-cache\"}]}"
# Expect first X-AT-Cache: MISS, second HIT
curl http://localhost:8080/v1/usage -H "Authorization: Bearer sk-at-dev"
docker compose --profile rust up --build -d gateway-rs
curl http://localhost:8081/health
```

## B. Local without Docker (verified)

Docker is not required for the smoke path. Automated script:

```powershell
# builds on release binary at gateway-rs/target/release/at-gateway-rs.exe
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/smoke_verify.ps1
```

What it proves:

1. Rust listens (default smoke ports `:18081`) — health `at-gateway-rs`
2. Client entry via Rust → `x-at-plane: rust`, first chat `x-at-cache: MISS`
3. Second identical chat → `x-at-cache: HIT` via raw RESP to the local stub
4. Python MemoryStore MISS→HIT on `:18080`

Manual equivalent:

```powershell
python scripts/resp_stub.py --port 16379
# Python with intentional bad REDIS_URL -> MemoryStore fallback
$env:REDIS_URL="redis://127.0.0.1:1/0"
$env:AT_API_KEYS="sk-at-dev"
python -m uvicorn at_utility.main:app --host 127.0.0.1 --port 18080
# Rust
$env:AT_RS_LISTEN="127.0.0.1:18081"
$env:AT_RS_REDIS="127.0.0.1:16379"
$env:AT_RS_PRIMARY="http://127.0.0.1:18080"
$env:AT_API_KEYS="sk-at-dev"
.\gateway-rs\target\release\at-gateway-rs.exe
```

When Docker Desktop is installed, prefer section A (real Redis + replica).

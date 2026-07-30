# Sync the canonical MCP client (src/ohm_mcp) into the standalone
# packages/ohm-mcp distribution before building/publishing it.
#
#   .\scripts\sync_ohm_mcp.ps1
#   python -m build packages/ohm-mcp
#   twine upload packages/ohm-mcp/dist/*

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root "src\ohm_mcp"
$dst = Join-Path $root "packages\ohm-mcp\src\ohm_mcp"

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Path (Join-Path $src "*.py") -Destination $dst -Force
Write-Host "Synced src/ohm_mcp -> packages/ohm-mcp/src/ohm_mcp"

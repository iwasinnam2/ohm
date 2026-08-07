"""MCP tool catalogue must stay an exact count of @mcp.tool handlers."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_INIT = REPO_ROOT / "src" / "ohm_mcp" / "__init__.py"
PKG_MCP_INIT = REPO_ROOT / "packages" / "ohm-mcp" / "src" / "ohm_mcp" / "__init__.py"

EXPECTED_TOOLS = frozenset(
    {
        "ohm_chat",
        "ohm_fetch_web",
        "ohm_usage",
        "ohm_models",
        "ohm_savings",
        "ohm_receipt",
        "ohm_providers",
        "ohm_policy",
    }
)


def _tools_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            # @mcp.tool() or @mcp.tool
            if isinstance(dec, ast.Call):
                dec = dec.func
            if isinstance(dec, ast.Attribute) and dec.attr == "tool":
                found.add(node.name)
                break
    return found


def test_mcp_tool_inventory_is_eight() -> None:
    tools = _tools_in(MCP_INIT)
    assert tools == EXPECTED_TOOLS
    assert len(tools) == 8


def test_packaged_mcp_mirrors_src() -> None:
    assert PKG_MCP_INIT.is_file()
    assert _tools_in(PKG_MCP_INIT) == _tools_in(MCP_INIT)


def test_ohm_receipt_skill_exists() -> None:
    skill = REPO_ROOT / ".cursor" / "skills" / "ohm-receipt" / "SKILL.md"
    assert skill.is_file()
    text = skill.read_text(encoding="utf-8")
    assert "ohm_receipt" in text

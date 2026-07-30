"""Machine-readable Ohm model catalog (Neon AI Gateway–style surface).

Ohm is a BYOK tollbooth: frontier models route to the customer's provider key.
``mock`` is local. Optional managed open-weight routes are marked for future use
but are not hosted here yet — the catalog documents routing honestly.
"""

from __future__ import annotations

from typing import Any

# Scopes a tenant key may hold (Neon-style granular credentials).
SCOPE_CHAT = "ohm:chat"
SCOPE_FETCH = "ohm:fetch"
SCOPE_ADMIN = "ohm:admin"
DEFAULT_SCOPES = (SCOPE_CHAT, SCOPE_FETCH)
ALL_SCOPES = frozenset({SCOPE_CHAT, SCOPE_FETCH, SCOPE_ADMIN})


def normalize_scopes(scopes: list[str] | None) -> list[str]:
    if not scopes:
        return list(DEFAULT_SCOPES)
    out: list[str] = []
    for s in scopes:
        s = (s or "").strip()
        if s in ALL_SCOPES and s not in out:
            out.append(s)
    return out or list(DEFAULT_SCOPES)


def has_scope(scopes: list[str] | None, needed: str) -> bool:
    held = set(scopes or DEFAULT_SCOPES)
    # Admin scope implies chat+fetch for ops keys that use tenant shape.
    if SCOPE_ADMIN in held:
        return True
    return needed in held


# Catalog entries — keep short OpenRouter-style ids; document route + BYOK.
MODEL_CATALOG: list[dict[str, Any]] = [
    {
        "id": "mock",
        "object": "model",
        "owned_by": "ohm",
        "provider": "ohm",
        "route": "local",
        "byok": False,
        "managed": True,
        "note": "Fully local mock — no upstream key. Default for offline/dev.",
    },
    {
        "id": "gpt-4o-mini",
        "object": "model",
        "owned_by": "openai",
        "provider": "openai",
        "route": "byok",
        "byok": True,
        "managed": False,
        "byok_header": "X-Ohm-Upstream-Key",
        "note": "OpenAI chat — send provider key as X-Ohm-Upstream-Key on cache miss.",
    },
    {
        "id": "gpt-4o",
        "object": "model",
        "owned_by": "openai",
        "provider": "openai",
        "route": "byok",
        "byok": True,
        "managed": False,
        "byok_header": "X-Ohm-Upstream-Key",
    },
    {
        "id": "o4-mini",
        "object": "model",
        "owned_by": "openai",
        "provider": "openai",
        "route": "byok",
        "byok": True,
        "managed": False,
        "byok_header": "X-Ohm-Upstream-Key",
    },
    {
        "id": "claude-3-5-sonnet-latest",
        "object": "model",
        "owned_by": "anthropic",
        "provider": "anthropic",
        "route": "byok",
        "byok": True,
        "managed": False,
        "byok_header": "X-Ohm-Upstream-Key",
        "note": "Anthropic Messages translated to OpenAI chat shape.",
    },
    {
        "id": "claude-sonnet-4-20250514",
        "object": "model",
        "owned_by": "anthropic",
        "provider": "anthropic",
        "route": "byok",
        "byok": True,
        "managed": False,
        "byok_header": "X-Ohm-Upstream-Key",
    },
]


def models_list_payload() -> dict[str, Any]:
    return {
        "object": "list",
        "data": list(MODEL_CATALOG),
        "byok_header": "X-Ohm-Upstream-Key",
        "billing_model": "seat_plus_meters",
        "note": (
            "Ohm rents the pipe (cache + compliant fetch), not the model. "
            "Non-mock models need X-Ohm-Upstream-Key on cache miss unless "
            "env/enterprise managed keys are configured."
        ),
        "docs": "https://www.withohm.dev/docs",
    }


def models_json_document() -> dict[str, Any]:
    """Public catalog document (Neon models.json analogue)."""
    return {
        "provider": "withohm",
        "api": "https://api.withohm.dev/v1",
        "local_edge": "http://localhost:8081/v1",
        "byok_header": "X-Ohm-Upstream-Key",
        "scopes": sorted(ALL_SCOPES),
        "default_scopes": list(DEFAULT_SCOPES),
        "models": MODEL_CATALOG,
        "routes": {
            "mock": "local",
            "gpt-* / o*": "openai BYOK",
            "claude-*": "anthropic BYOK",
        },
    }

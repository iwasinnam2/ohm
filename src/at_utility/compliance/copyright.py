"""Copyright / database-right oriented excerpt caps for retrieved public pages."""

from __future__ import annotations

import re
from dataclasses import dataclass


_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INDENTED_CODE_RE = re.compile(r"(?:(?:^|\n)(?: {4}|\t).*){12,}")


@dataclass
class ExcerptResult:
    text: str
    truncated: bool
    chars_before: int
    chars_after: int
    code_blocks_stripped: int


def strip_large_code_blocks(text: str, *, min_fence_chars: int = 800) -> tuple[str, int]:
    """Replace large fenced/indented code regions with a short placeholder."""
    stripped = 0

    def _fence(m: re.Match[str]) -> str:
        nonlocal stripped
        block = m.group(0)
        if len(block) >= min_fence_chars:
            stripped += 1
            return "\n[CODE_EXCERPT_OMITTED — copyright minimisation]\n"
        return block

    out = _CODE_FENCE_RE.sub(_fence, text or "")
    def _indent(m: re.Match[str]) -> str:
        nonlocal stripped
        stripped += 1
        return "\n[CODE_EXCERPT_OMITTED — copyright minimisation]\n"

    out = _INDENTED_CODE_RE.sub(_indent, out)
    return out, stripped


def clamp_excerpt_chars(
    requested: int | None,
    *,
    ceiling: int,
) -> int:
    """Never allow a client to raise excerpt size above the operator ceiling.

    ``requested is None`` → use ceiling. ``requested <= 0`` → treat as ceiling
    (caps must stay on). Values above ceiling are clamped down.
    """
    if ceiling <= 0:
        raise ValueError("excerpt ceiling must be positive")
    if requested is None or requested <= 0:
        return ceiling
    return min(int(requested), ceiling)


def apply_excerpt_cap(
    text: str,
    *,
    max_chars: int = 4000,
    strip_code: bool = True,
) -> ExcerptResult:
    raw = text or ""
    before = len(raw)
    code_stripped = 0
    body = raw
    if strip_code:
        body, code_stripped = strip_large_code_blocks(body)
    truncated = False
    if max_chars > 0 and len(body) > max_chars:
        body = body[: max_chars].rstrip() + "\n\n[EXCERPT_TRUNCATED — short quotation for retrieval only]"
        truncated = True
    return ExcerptResult(
        text=body,
        truncated=truncated or code_stripped > 0,
        chars_before=before,
        chars_after=len(body),
        code_blocks_stripped=code_stripped,
    )


def cap_total_context(parts: list[str], *, max_chars: int = 12000) -> str:
    """Join markdown parts under a total character budget."""
    if max_chars <= 0:
        return "\n\n".join(parts)
    out: list[str] = []
    used = 0
    for part in parts:
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(part) <= remaining:
            out.append(part)
            used += len(part) + 2
        else:
            out.append(
                part[:remaining].rstrip()
                + "\n\n[CONTEXT_TRUNCATED — total web context budget]"
            )
            break
    return "\n\n".join(out)

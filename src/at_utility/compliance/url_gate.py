"""URL authorization gate — public http(s) only; block credentialed / private patterns."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse, unquote


@dataclass(frozen=True)
class UrlGateResult:
    allowed: bool
    code: str
    reason: str


# Paths that usually indicate login / account / private API surfaces
_BLOCKED_PATH_FRAGMENTS: tuple[str, ...] = (
    "/login",
    "/signin",
    "/sign-in",
    "/signup",
    "/sign-up",
    "/account/",
    "/accounts/",
    "/auth/",
    "/oauth/",
    "/session/",
    "/sso/",
    "/api/private",
    "/api/internal",
    "/admin/",
    "/settings/privacy",
    "/messages/",
    "/inbox/",
    "/dm/",
    "/direct_messages",
    "/friends/",
    "/paywall",
    "/checkout/",
    "/billing/",
)

# Host patterns commonly associated with private social / messaging (bulk profile scrape = High)
_HEIGHTENED_HOST_HINTS: tuple[str, ...] = (
    "accounts.snapchat.com",
    "app.snapchat.com",
    "www.snapchat.com",
    "snapchat.com",
)

_BLOCKED_SCHEMES = frozenset({"file", "ftp", "data", "javascript", "chrome", "about"})

# Cloud metadata / link-local specials
_BLOCKED_LITERAL_HOSTS = frozenset(
    {
        "metadata.google.internal",
        "metadata",
        "169.254.169.254",
    }
)


def gate_url(url: str, *, resolve_dns: bool = True) -> UrlGateResult:
    """Return whether a URL may be fetched under Ohm's public-only policy.

    When resolve_dns is True (default), resolve the hostname and deny if any
    address is private, loopback, link-local, or otherwise non-public (SSRF /
    DNS-rebinding mitigation).
    """
    raw = (url or "").strip()
    if not raw:
        return UrlGateResult(False, "empty_url", "URL is empty")

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme in _BLOCKED_SCHEMES:
        return UrlGateResult(False, "blocked_scheme", f"Scheme '{scheme}' is not allowed")
    if scheme not in ("http", "https"):
        return UrlGateResult(False, "unsupported_scheme", "Only http/https public URLs are allowed")

    # Credentials embedded in URL ⇒ unauthorized-access pattern
    if parsed.username or parsed.password:
        return UrlGateResult(
            False,
            "embedded_credentials",
            "URLs must not contain usernames or passwords (unauthorized access risk)",
        )

    host = (parsed.hostname or "").lower()
    if not host:
        return UrlGateResult(False, "missing_host", "URL host is required")

    if host in _BLOCKED_LITERAL_HOSTS:
        return UrlGateResult(
            False,
            "metadata_target",
            "Cloud metadata / link-local targets are not allowed",
        )

    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or host.endswith(".local"):
        return UrlGateResult(False, "local_target", "Local/loopback targets are not allowed")

    # Block link-local / private IP literals (SSRF + non-public)
    if _is_private_or_link_local_host(host):
        return UrlGateResult(
            False,
            "private_network",
            "Private/link-local network targets are not allowed",
        )

    # Account/app hosts before path checks (CFAA/CMA unauthorized-access risk)
    if host.startswith("accounts.") or host.startswith("app."):
        return UrlGateResult(
            False,
            "private_platform_host",
            "Account/app hosts are out of bounds (CFAA/CMA unauthorized-access risk)",
        )
    if any(h == host or host.endswith("." + h) for h in _HEIGHTENED_HOST_HINTS):
        if host.startswith("accounts.") or host.startswith("app.") or "/oauth" in (
            parsed.path or ""
        ).lower():
            return UrlGateResult(
                False,
                "private_platform_host",
                "Private platform auth surfaces are out of bounds",
            )

    path = unquote((parsed.path or "").lower())
    query = unquote((parsed.query or "").lower())
    combined = f"{path}?{query}"

    for frag in _BLOCKED_PATH_FRAGMENTS:
        if frag in combined:
            return UrlGateResult(
                False,
                "gated_surface",
                f"Path suggests login/account/private surface ('{frag}') — public pages only",
            )

    # Query params that look like session theft
    for token_key in ("access_token=", "refresh_token=", "id_token=", "sessionid=", "auth_token="):
        if token_key in query:
            return UrlGateResult(
                False,
                "token_in_url",
                "URL appears to carry session/auth tokens — prohibited",
            )

    if resolve_dns:
        dns = _dns_resolves_to_public(host)
        if not dns.allowed:
            return dns

    return UrlGateResult(True, "ok", "Public http(s) URL accepted for policy check")


def _is_private_or_link_local_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        pass
    # Literal IPv4 private ranges (fallback for odd hosts)
    if host.count(".") == 3 and all(p.isdigit() for p in host.split(".")):
        parts = [int(p) for p in host.split(".")]
        a, b = parts[0], parts[1]
        if a == 10:
            return True
        if a == 172 and 16 <= b <= 31:
            return True
        if a == 192 and b == 168:
            return True
        if a == 169 and b == 254:
            return True
        if a == 127:
            return True
    if host.startswith("fc") or host.startswith("fd") or host.startswith("fe80"):
        return True
    return False


def _ip_is_non_public(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return True
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
        or ip in (ipaddress.ip_address("169.254.169.254"),)
    )


def _dns_resolves_to_public(host: str) -> UrlGateResult:
    """Resolve hostname; deny if any A/AAAA is non-public (DNS rebinding / SSRF)."""
    try:
        # Skip resolve for literal IPs already checked
        ipaddress.ip_address(host)
        return UrlGateResult(True, "ok", "Literal IP already checked")
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return UrlGateResult(
            False,
            "dns_unresolvable",
            "Hostname could not be resolved — refusing fetch",
        )
    except OSError as exc:
        return UrlGateResult(
            False,
            "dns_error",
            f"DNS resolution failed — refusing fetch ({exc})",
        )

    if not infos:
        return UrlGateResult(
            False,
            "dns_unresolvable",
            "Hostname resolved to no addresses — refusing fetch",
        )

    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        addr = sockaddr[0]
        if _ip_is_non_public(addr):
            return UrlGateResult(
                False,
                "dns_private_target",
                "Hostname resolves to a private/link-local/metadata address — not allowed",
            )
    return UrlGateResult(True, "ok", "DNS resolves to public addresses")

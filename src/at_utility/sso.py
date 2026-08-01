"""OIDC SSO sessions for org console (humans). Agents keep bearer API keys."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Optional

from at_utility.config import Settings
from at_utility.orgs import OrgRegistry, new_session_token
from at_utility.redis_store import CacheStore


@dataclass
class SsoSession:
    token: str
    org_id: str
    email: str
    role: str
    created_at: int
    expires_at: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(raw: str) -> "SsoSession":
        data = json.loads(raw)
        return SsoSession(**{k: data[k] for k in SsoSession.__dataclass_fields__ if k in data})

    def is_expired(self, now: int | None = None) -> bool:
        return (now if now is not None else int(time.time())) >= self.expires_at


class SsoService:
    SESSION_TTL = 12 * 3600

    def __init__(self, store: CacheStore, settings: Settings, orgs: OrgRegistry):
        self._store = store
        self._settings = settings
        self._orgs = orgs

    def _session_key(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"at:global:sso_session:{digest}"

    def configured(self) -> bool:
        """True when OIDC is configured or local-dev SSO secret is set."""
        return bool(
            self._settings.at_oidc_issuer
            and self._settings.at_oidc_client_id
            and self._settings.at_oidc_client_secret
        ) or bool(self._settings.at_sso_dev_secret)

    def authorize_url(self, *, state: str, redirect_uri: str) -> str:
        if not self._settings.at_oidc_issuer:
            return ""
        base = self._settings.at_oidc_issuer.rstrip("/")
        auth_ep = self._settings.at_oidc_authorize_url or f"{base}/authorize"
        q = urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": self._settings.at_oidc_client_id,
                "redirect_uri": redirect_uri,
                "scope": self._settings.at_oidc_scopes,
                "state": state,
            }
        )
        return f"{auth_ep}?{q}"

    async def exchange_code(
        self, *, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange auth code for claims (email). Raises ValueError on failure."""
        token_url = self._settings.at_oidc_token_url or (
            self._settings.at_oidc_issuer.rstrip("/") + "/oauth/token"
        )
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._settings.at_oidc_client_id,
                "client_secret": self._settings.at_oidc_client_secret,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            token_url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as res:
            tok = json.loads(res.read().decode("utf-8"))
        # Prefer userinfo; fallback to id_token payload (dev-only simplistic).
        email = ""
        if self._settings.at_oidc_userinfo_url and tok.get("access_token"):
            ureq = urllib.request.Request(
                self._settings.at_oidc_userinfo_url,
                headers={"Authorization": f"Bearer {tok['access_token']}"},
            )
            with urllib.request.urlopen(ureq, timeout=20) as ures:
                info = json.loads(ures.read().decode("utf-8"))
            email = str(info.get("email") or info.get("preferred_username") or "")
        if not email and tok.get("id_token"):
            # Non-verifying decode for email claim only when explicitly allowed.
            if self._settings.at_oidc_allow_unverified_id_token:
                parts = str(tok["id_token"]).split(".")
                if len(parts) >= 2:
                    import base64

                    pad = "=" * (-len(parts[1]) % 4)
                    payload = json.loads(
                        base64.urlsafe_b64decode(parts[1] + pad).decode("utf-8")
                    )
                    email = str(payload.get("email") or "")
        if not email:
            raise ValueError("OIDC response missing email claim")
        return {"email": email.lower(), "raw": tok}

    async def mint_session(
        self, *, org_id: str, email: str, role: str = "member"
    ) -> SsoSession:
        token = new_session_token()
        now = int(time.time())
        session = SsoSession(
            token=token,
            org_id=org_id,
            email=email.lower(),
            role=role,
            created_at=now,
            expires_at=now + self.SESSION_TTL,
        )
        await self._store.set(
            self._session_key(token),
            session.to_json(),
            ttl_seconds=self.SESSION_TTL,
        )
        return session

    async def resolve_session(self, token: str) -> Optional[SsoSession]:
        if not token:
            return None
        raw = await self._store.get(self._session_key(token))
        if not raw:
            return None
        session = SsoSession.from_json(raw)
        if session.is_expired():
            return None
        return session

    async def dev_login(
        self, *, email: str, org_id: str, secret: str
    ) -> SsoSession:
        """Local/dev SSO: shared secret mints a session without IdP."""
        expected = self._settings.at_sso_dev_secret
        if not expected or secret != expected:
            raise PermissionError("invalid SSO dev secret")
        org = await self._orgs.get(org_id)
        if not org:
            raise ValueError("org not found")
        role = org.members.get(email.lower(), "member")
        if email.lower() not in org.members:
            await self._orgs.add_member(org_id, email, "member")
            role = "member"
        return await self.mint_session(org_id=org_id, email=email, role=role)

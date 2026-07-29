"""Stripe customer ledger helpers (optional dependency).

Billing model: monthly subscription seat + Billing Meters for web_fetch /
cache_hit / cache_miss. Redis ledger remains ops source of truth.
"""

from __future__ import annotations

import logging
import secrets
import string
from typing import Any, Optional

from at_utility.config import Settings

log = logging.getLogger("at_utility.stripe")

BILLING_MODEL = "seat_plus_meters"


def stripe_configured(settings: Settings) -> bool:
    return bool(settings.stripe_secret_key)


def resolve_checkout_urls(
    settings: Settings, success_url: str, cancel_url: str
) -> tuple[str, str]:
    """Prefer explicit body URLs unless they are still example.com placeholders."""
    success = success_url.strip()
    cancel = cancel_url.strip()
    if not success or "example.com" in success:
        success = settings.stripe_checkout_success_url
    if not cancel or "example.com" in cancel:
        cancel = settings.stripe_checkout_cancel_url
    return success, cancel


def _integration_identifier() -> str:
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(8))
    return f"ohm_checkout_{suffix}"


def _meter_line_items(settings: Settings) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for price_id in (
        settings.stripe_price_meter_web_fetch,
        settings.stripe_price_meter_cache_hit,
        settings.stripe_price_meter_cache_miss,
    ):
        if price_id:
            items.append({"price": price_id})
    return items


def create_checkout_session(
    settings: Settings,
    *,
    tenant_id: str,
    plan: str,
    success_url: str,
    cancel_url: str,
    customer_email: str = "",
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session (subscription seat + optional meters)
    for payg or enterprise.
    """
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    try:
        import stripe
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install stripe: pip install 'at-utility[billing]'") from exc

    stripe.api_key = settings.stripe_secret_key
    price = (
        settings.stripe_price_enterprise
        if plan == "enterprise"
        else settings.stripe_price_payg
    )
    if not price:
        raise RuntimeError(f"Stripe price id missing for plan={plan}")

    success_url, cancel_url = resolve_checkout_urls(settings, success_url, cancel_url)
    line_items: list[dict[str, Any]] = [{"price": price, "quantity": 1}]
    line_items.extend(_meter_line_items(settings))

    params: dict[str, Any] = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items": line_items,
        "client_reference_id": tenant_id,
        "metadata": {
            "tenant_id": tenant_id,
            "plan": plan,
            "billing_model": BILLING_MODEL,
        },
        "subscription_data": {
            "metadata": {
                "tenant_id": tenant_id,
                "plan": plan,
                "billing_model": BILLING_MODEL,
            }
        },
        "integration_identifier": _integration_identifier(),
    }
    if customer_email.strip():
        params["customer_email"] = customer_email.strip()

    try:
        session = stripe.checkout.Session.create(**params)
    except TypeError:
        params.pop("integration_identifier", None)
        session = stripe.checkout.Session.create(**params)
    except Exception as exc:
        # Older API versions reject unknown params
        if "integration_identifier" in str(exc):
            params.pop("integration_identifier", None)
            session = stripe.checkout.Session.create(**params)
        else:
            raise
    return {
        "id": session.id,
        "url": session.url,
        "tenant_id": tenant_id,
        "plan": plan,
        "billing_model": BILLING_MODEL,
    }


def report_meter_event(
    settings: Settings,
    *,
    event_name: str,
    stripe_customer_id: str,
    value: int | float,
) -> bool:
    """Fire a Stripe Billing Meter event. Returns False if skipped/failed."""
    if not settings.stripe_secret_key or not stripe_customer_id or not event_name:
        return False
    if value <= 0:
        return False
    try:
        import stripe
    except ImportError:
        return False
    try:
        stripe.api_key = settings.stripe_secret_key
        stripe.billing.MeterEvent.create(
            event_name=event_name,
            payload={
                "stripe_customer_id": stripe_customer_id,
                "value": str(int(value) if float(value).is_integer() else value),
            },
        )
        return True
    except Exception as exc:  # noqa: BLE001 — never break chat path on meter sync
        log.warning("stripe meter event failed name=%s err=%s", event_name, exc)
        return False


def construct_webhook_event(
    settings: Settings, payload: bytes, signature: str
) -> Any:
    if not settings.stripe_webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")
    try:
        import stripe
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install stripe: pip install 'at-utility[billing]'") from exc
    return stripe.Webhook.construct_event(
        payload, signature, settings.stripe_webhook_secret
    )


def apply_webhook_to_status(event_type: str) -> Optional[str]:
    """Map Stripe event types to tenant status updates."""
    if event_type in (
        "customer.subscription.deleted",
        "invoice.payment_failed",
    ):
        return "suspended"
    if event_type in (
        "checkout.session.completed",
        "customer.subscription.updated",
        "invoice.paid",
    ):
        return "active"
    return None

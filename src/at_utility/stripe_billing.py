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


def meter_prices_configured(settings: Settings) -> bool:
    return bool(
        settings.stripe_price_meter_web_fetch
        and settings.stripe_price_meter_cache_hit
        and settings.stripe_price_meter_cache_miss
    )


def require_meter_prices(settings: Settings, plan: str) -> None:
    """Fail closed for Intermediate (payg) when meters required."""
    if plan != "payg":
        return
    need = (
        settings.at_require_meter_prices
        or settings.at_env.strip().lower() == "production"
    )
    if need and not meter_prices_configured(settings):
        raise RuntimeError(
            "Intermediate checkout requires STRIPE_PRICE_METER_WEB_FETCH, "
            "STRIPE_PRICE_METER_CACHE_HIT, and STRIPE_PRICE_METER_CACHE_MISS "
            "(set AT_ENV=production or AT_REQUIRE_METER_PRICES=true). "
            "Create meters with scripts/stripe_create_meters.sh"
        )


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
    Create a Stripe Checkout Session (subscription seat + meters)
    for payg or enterprise.
    """
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    require_meter_prices(settings, plan)
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
    if plan == "payg" and not _meter_line_items(settings):
        # Defense in depth when require_meter_prices was skipped (non-prod)
        log.warning(
            "checkout plan=payg without meter Prices — seat-only subscription"
        )
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


def create_credit_pack_session(
    settings: Settings,
    *,
    tenant_id: str,
    success_url: str,
    cancel_url: str,
    stripe_customer_id: str = "",
    customer_email: str = "",
) -> dict[str, Any]:
    """One-time $29 credit pack Checkout (mode=payment).

    The webhook applies the paid amount as a negative customer balance so it
    offsets future metered invoices (prepaid allowance, not a seat).
    """
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    if not settings.stripe_price_credit_pack:
        raise RuntimeError(
            "STRIPE_PRICE_CREDIT_PACK is not configured — create it with "
            "scripts/stripe_create_test_prices.sh"
        )
    try:
        import stripe
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install stripe: pip install 'at-utility[billing]'") from exc

    stripe.api_key = settings.stripe_secret_key
    success_url, cancel_url = resolve_checkout_urls(settings, success_url, cancel_url)
    params: dict[str, Any] = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items": [
            {"price": settings.stripe_price_credit_pack, "quantity": 1}
        ],
        "client_reference_id": tenant_id,
        "metadata": {
            "tenant_id": tenant_id,
            "purpose": "credit_pack",
            "billing_model": BILLING_MODEL,
        },
    }
    if stripe_customer_id:
        params["customer"] = stripe_customer_id
    elif customer_email.strip():
        params["customer_email"] = customer_email.strip()
    session = stripe.checkout.Session.create(**params)
    return {
        "id": session.id,
        "url": session.url,
        "tenant_id": tenant_id,
        "purpose": "credit_pack",
    }


def apply_credit_pack_balance(
    settings: Settings,
    *,
    stripe_customer_id: str,
    amount_cents: int,
    currency: str = "usd",
) -> bool:
    """Credit a paid pack to the customer balance (offsets future invoices)."""
    if not settings.stripe_secret_key or not stripe_customer_id or amount_cents <= 0:
        return False
    try:
        import stripe
    except ImportError:
        return False
    try:
        stripe.api_key = settings.stripe_secret_key
        stripe.Customer.create_balance_transaction(
            stripe_customer_id,
            amount=-abs(int(amount_cents)),
            currency=currency or "usd",
            description="withOhm credit pack — prepaid toward metered usage",
        )
        return True
    except Exception as exc:  # noqa: BLE001 — surfaced via logs; webhook still 200s
        log.warning("credit pack balance apply failed cus=%s err=%s", stripe_customer_id, exc)
        return False


def report_meter_event(
    settings: Settings,
    *,
    event_name: str,
    stripe_customer_id: str,
    value: int | float,
    identifier: str = "",
) -> bool:
    """Fire a Stripe Billing Meter event. Returns False if skipped/failed.

    ``identifier`` deduplicates: Stripe rejects a repeated identifier within the
    24h window, so retries of the same logical event never double-bill.
    """
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
        params: dict[str, Any] = {
            "event_name": event_name,
            "payload": {
                "stripe_customer_id": stripe_customer_id,
                "value": str(int(value) if float(value).is_integer() else value),
            },
        }
        if identifier:
            # Stripe caps identifier length at 100 chars
            params["identifier"] = identifier[:100]
        stripe.billing.MeterEvent.create(**params)
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


def apply_webhook_to_status(
    event_type: str,
    *,
    subscription_status: str = "",
) -> Optional[str]:
    """Map Stripe events to tenant status.

    Do **not** suspend on the first ``invoice.payment_failed`` — Stripe Smart
    Retries + customer reminder emails need a 1–14 day collection window.
    Hard cutover: subscription deleted / unpaid / canceled, or uncollectible invoice.
    """
    if event_type in (
        "customer.subscription.deleted",
        "invoice.marked_uncollectible",
    ):
        return "suspended"
    if event_type == "customer.subscription.updated":
        st = (subscription_status or "").strip().lower()
        if st in ("canceled", "unpaid", "incomplete_expired"):
            return "suspended"
        if st in ("active", "trialing"):
            return "active"
        # past_due / incomplete: keep pipe open for remediating payment method
        return None
    if event_type in (
        "checkout.session.completed",
        "invoice.paid",
    ):
        return "active"
    return None

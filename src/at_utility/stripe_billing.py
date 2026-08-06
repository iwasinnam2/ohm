"""Stripe customer ledger helpers (optional dependency).

Billing model: monthly subscription seat + Billing Meters for web_fetch /
cache_hit / cache_miss. Redis ledger remains ops source of truth.
"""

from __future__ import annotations

import logging
import secrets
import string
import time
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


def meter_price_ids(settings: Settings) -> list[str]:
    """Configured metered Price IDs (web_fetch, cache_hit, cache_miss)."""
    return [
        price_id
        for price_id in (
            settings.stripe_price_meter_web_fetch,
            settings.stripe_price_meter_cache_hit,
            settings.stripe_price_meter_cache_miss,
        )
        if price_id
    ]


def attach_meter_prices_to_subscription(
    settings: Settings, *, subscription_id: str
) -> int:
    """Attach metered Prices to a seat-only subscription. Idempotent.

    Checkout shows only the membership/commit seat so the hosted page does not
    list hit/miss/fetch as separate charges. Meters are added here on
    ``checkout.session.completed``. Returns the number of items newly created.
    """
    if not settings.stripe_secret_key or not subscription_id:
        return 0
    wanted = meter_price_ids(settings)
    if not wanted:
        return 0
    try:
        import stripe
    except ImportError:
        return 0
    try:
        stripe.api_key = settings.stripe_secret_key
        sub = stripe.Subscription.retrieve(
            subscription_id, expand=["items.data.price"]
        )
        items = sub.get("items") if isinstance(sub, dict) else getattr(sub, "items", None)
        data = (
            items.get("data")
            if isinstance(items, dict)
            else getattr(items, "data", None)
        ) or []
        existing: set[str] = set()
        for item in data:
            price = (
                item.get("price")
                if isinstance(item, dict)
                else getattr(item, "price", None)
            )
            price_id = (
                price.get("id")
                if isinstance(price, dict)
                else getattr(price, "id", None)
            )
            if price_id:
                existing.add(str(price_id))
        missing = [pid for pid in wanted if pid not in existing]
        if not missing:
            return 0
        stripe.Subscription.modify(
            subscription_id,
            items=[{"price": pid} for pid in missing],
            proration_behavior="none",
        )
        return len(missing)
    except Exception as exc:  # noqa: BLE001 — webhook must still 200
        log.warning(
            "attach meter prices failed sub=%s err=%s", subscription_id, exc
        )
        return 0


def commit_tier_prices(settings: Settings) -> dict[str, str]:
    """Configured commit tiers (rate card v2) → Stripe seat Price IDs."""
    tiers = {
        "c29": settings.stripe_price_commit_c29,
        "c99": settings.stripe_price_commit_c99,
        "c499": settings.stripe_price_commit_c499,
    }
    return {tier: price for tier, price in tiers.items() if price}


def commit_included_usd(settings: Settings, tier: str) -> float:
    return {
        "c29": settings.at_commit_included_usd_c29,
        "c99": settings.at_commit_included_usd_c99,
        "c499": settings.at_commit_included_usd_c499,
    }.get(tier, 0.0)


def _apply_tax_params(settings: Settings, params: dict[str, Any]) -> None:
    """Stripe Tax on Checkout — gated on STRIPE_AUTOMATIC_TAX because session
    creation fails if the dashboard has no origin address / active Stripe Tax.
    Prices are created tax_behavior=exclusive, so tax adds on top of list."""
    if not settings.stripe_automatic_tax:
        return
    params["automatic_tax"] = {"enabled": True}
    params["billing_address_collection"] = "required"
    params["tax_id_collection"] = {"enabled": True}


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
    plan: str,
    success_url: str,
    cancel_url: str,
    tenant_id: str = "",
    pending_id: str = "",
    customer_email: str = "",
    commit: str = "",
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session for payg or enterprise.

    Hosted Checkout line items are **seat only** ($0 membership or a commit
    tier) so hit/miss/fetch do not appear as charges. Metered Prices are
    attached to the subscription on ``checkout.session.completed`` via
    :func:`attach_meter_prices_to_subscription`. Included usage for commit
    tiers is granted per cycle by the invoice.paid webhook.

    Self-serve uses ``pending_id`` (no API key until Checkout completes).
    Admin flows may pass an already-issued ``tenant_id``.
    """
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    require_meter_prices(settings, plan)
    try:
        import stripe
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install stripe: pip install 'at-utility[billing]'") from exc

    stripe.api_key = settings.stripe_secret_key
    commit = commit.strip().lower()
    if plan == "enterprise":
        price = settings.stripe_price_enterprise
        commit = ""
    elif commit:
        price = commit_tier_prices(settings).get(commit, "")
        if not price:
            raise RuntimeError(
                f"Commit tier {commit!r} is not configured — create prices "
                "with scripts/stripe_create_prices_v2.sh"
            )
    else:
        price = settings.stripe_price_payg
    if not price:
        raise RuntimeError(f"Stripe price id missing for plan={plan}")

    success_url, cancel_url = resolve_checkout_urls(settings, success_url, cancel_url)
    # Seat only on the hosted page — meters attach post-checkout (webhook).
    line_items: list[dict[str, Any]] = [{"price": price, "quantity": 1}]
    if plan == "payg" and not meter_prices_configured(settings):
        # Defense in depth when require_meter_prices was skipped (non-prod)
        log.warning(
            "checkout plan=payg without meter Prices — seat-only subscription"
        )
    ref = (pending_id or tenant_id or "").strip()
    if not ref:
        raise RuntimeError("checkout requires pending_id or tenant_id")
    shared_meta: dict[str, str] = {
        "plan": plan,
        "billing_model": BILLING_MODEL,
    }
    if pending_id:
        shared_meta["pending_id"] = pending_id.strip()
    if tenant_id and not pending_id:
        shared_meta["tenant_id"] = tenant_id.strip()
    if commit:
        shared_meta["commit_tier"] = commit
    params: dict[str, Any] = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items": line_items,
        "client_reference_id": ref[:200],
        "metadata": dict(shared_meta),
        "subscription_data": {"metadata": dict(shared_meta)},
        "integration_identifier": _integration_identifier(),
    }
    _apply_tax_params(settings, params)
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
    result = {
        "id": session.id,
        "url": session.url,
        "tenant_id": tenant_id,
        "plan": plan,
        "billing_model": BILLING_MODEL,
    }
    if commit:
        result["commit_tier"] = commit
    return result


def grant_commit_included_credit(
    settings: Settings,
    *,
    stripe_customer_id: str,
    tier: str,
    invoice_id: str,
) -> float:
    """Grant a commit tier's included metered usage for one billing cycle.

    Uses a Billing Credit Grant scoped to metered prices so the credit can
    never offset the seat fee itself (a raw customer-balance credit would eat
    the next cycle's commit, making the tier self-cancelling). Idempotent per
    invoice via Stripe idempotency keys, so webhook redelivery cannot
    double-grant. Returns the granted USD (0.0 if skipped/failed).
    """
    amount_usd = commit_included_usd(settings, tier)
    if (
        not settings.stripe_secret_key
        or not stripe_customer_id
        or not invoice_id
        or amount_usd <= 0
    ):
        return 0.0
    try:
        import stripe
    except ImportError:
        return 0.0
    try:
        stripe.api_key = settings.stripe_secret_key
        stripe.billing.CreditGrant.create(
            customer=stripe_customer_id,
            name=f"withOhm {tier} included usage",
            category="paid",
            amount={
                "type": "monetary",
                "monetary": {
                    "currency": "usd",
                    "value": int(round(amount_usd * 100)),
                },
            },
            applicability_config={"scope": {"price_type": "metered"}},
            # Cycle + slack: unused included usage does not stockpile forever.
            expires_at=int(time.time()) + 40 * 86400,
            metadata={"commit_tier": tier, "invoice_id": invoice_id},
            idempotency_key=f"ohm-commit-credit-{invoice_id}"[:255],
        )
        return amount_usd
    except Exception as exc:  # noqa: BLE001 — webhook must still 200
        log.warning(
            "commit credit grant failed cus=%s tier=%s invoice=%s err=%s",
            stripe_customer_id,
            tier,
            invoice_id,
            exc,
        )
        return 0.0


def commit_tier_for_invoice(settings: Settings, invoice_obj: Any) -> str:
    """Identify the commit tier on a paid invoice by scanning line-item price
    IDs against the configured commit Prices. Returns "" when none match."""
    prices = commit_tier_prices(settings)
    if not prices:
        return ""
    by_price = {price_id: tier for tier, price_id in prices.items()}

    def _get(obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        try:
            return obj[key]
        except Exception:  # noqa: BLE001
            return getattr(obj, key, None)

    lines = _get(invoice_obj, "lines")
    data = _get(lines, "data") if lines is not None else None
    for line in data or []:
        price = _get(line, "price")
        price_id = _get(price, "id") if price is not None else None
        # Newer API shapes carry pricing.price_details.price instead of price
        if not price_id:
            pricing = _get(line, "pricing")
            details = _get(pricing, "price_details") if pricing is not None else None
            price_id = _get(details, "price") if details is not None else None
        if price_id and str(price_id) in by_price:
            return by_price[str(price_id)]
    return ""


def create_credit_pack_session(
    settings: Settings,
    *,
    tenant_id: str,
    success_url: str,
    cancel_url: str,
    stripe_customer_id: str = "",
    customer_email: str = "",
) -> dict[str, Any]:
    """RETIRED (rate card v2): one-time credit pack Checkout (mode=payment).

    Superseded by commit tiers — kept only so any in-flight v1 sessions and
    their webhooks resolve cleanly. Do not wire new surfaces to this.
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

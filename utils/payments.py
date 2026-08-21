"""
Payment helpers for Payoneer and PayPal.

Payoneer is used via payment / request links (no full Checkout API like Stripe).
PayPal can use simple PayPal.me or invoice links, or full API later.

Configure your real links below or via environment / Streamlit secrets.
Never commit real secrets to git.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import os

# ---------------------------------------------------------------------------
# Plan definitions (keep in sync with the UI)
# ---------------------------------------------------------------------------

PLANS = {
    "payg_100": {
        "name": "Pay-as-you-go – 100 words",
        "price_usd": 9.00,
        "type": "one_time",
        "words": 100,
        "description": "One block of 100 words",
    },
    "monthly_75": {
        "name": "Monthly Subscription",
        "price_usd": 75.00,
        "type": "subscription",
        "interval": "month",
        "description": "Unlimited generation for one month (fair use)",
    },
}


# ---------------------------------------------------------------------------
# Configure your real payment links here (or load from secrets / env)
# ---------------------------------------------------------------------------

def _get_payoneer_link(plan_id: str) -> Optional[str]:
    """
    Return the Payoneer payment / request link for the given plan.
    Prefer Streamlit secrets or environment variables in production.
    """
    # Example: set these in Streamlit Cloud secrets or environment:
    # PAYONEER_LINK_PAYG = "https://payoneer.com/..."
    # PAYONEER_LINK_MONTHLY = "https://payoneer.com/..."
    if plan_id == "payg_100":
        return os.getenv("PAYONEER_LINK_PAYG") or None
    if plan_id == "monthly_75":
        return os.getenv("PAYONEER_LINK_MONTHLY") or None
    return None


def _get_paypal_link(plan_id: str) -> Optional[str]:
    """
    Return a PayPal.me or invoice link for the given plan.
    """
    if plan_id == "payg_100":
        return os.getenv("PAYPAL_LINK_PAYG") or None
    if plan_id == "monthly_75":
        return os.getenv("PAYPAL_LINK_MONTHLY") or None
    return None


# ---------------------------------------------------------------------------
# Public helpers used by the app
# ---------------------------------------------------------------------------

def get_payoneer_payment_link(plan_id: str) -> Dict[str, Any]:
    """
    Return a Payoneer payment link for the selected plan.
    """
    plan = PLANS.get(plan_id)
    if not plan:
        return {"url": None, "message": f"Unknown plan: {plan_id}"}

    url = _get_payoneer_link(plan_id)
    if url:
        return {"url": url, "plan": plan}

    return {
        "url": None,
        "message": (
            f"Payoneer link for '{plan['name']}' (${plan['price_usd']}) is not set yet. "
            "Add PAYONEER_LINK_PAYG / PAYONEER_LINK_MONTHLY in secrets or environment."
        ),
        "plan": plan,
    }


def create_paypal_order(plan_id: str, return_url: str = "", cancel_url: str = "") -> Dict[str, Any]:
    """
    Return a simple PayPal payment link (PayPal.me or invoice).
    Full PayPal REST API can be added later if needed.
    """
    plan = PLANS.get(plan_id)
    if not plan:
        return {"approve_url": None, "message": f"Unknown plan: {plan_id}"}

    url = _get_paypal_link(plan_id)
    if url:
        return {"approve_url": url, "plan": plan}

    return {
        "approve_url": None,
        "message": (
            f"PayPal link for '{plan['name']}' (${plan['price_usd']}) is not set yet. "
            "Add PAYPAL_LINK_PAYG / PAYPAL_LINK_MONTHLY in secrets or environment."
        ),
        "plan": plan,
    }

"""
Payment integration stubs for Stripe and PayPal.

This module is intentionally incomplete until you add your own API keys.
When you are ready:

1. Create a Stripe account → https://dashboard.stripe.com
2. Create a PayPal Business account (optional) → https://developer.paypal.com
3. Put the keys in Streamlit secrets or environment variables (never commit them).
4. Replace the stub functions below with real API calls.

Recommended flow for Streamlit:
- Use Stripe Checkout Sessions (hosted page) or Payment Links for simplicity.
- For subscriptions use Stripe Billing (Products + Prices + Checkout in subscription mode).
- After successful payment, Stripe redirects back to your app with a session_id.
- Verify the session server-side (or via webhook) and set a session_state flag
  or store the customer/subscription status in a small database.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import os

# ---------------------------------------------------------------------------
# Configuration (load from secrets / env – never hard-code real keys)
# ---------------------------------------------------------------------------

def get_stripe_secret_key() -> Optional[str]:
    """Return Stripe secret key from environment or Streamlit secrets."""
    # In production you would do:
    # import streamlit as st
    # return st.secrets.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY")
    return os.getenv("STRIPE_SECRET_KEY")


def get_stripe_publishable_key() -> Optional[str]:
    return os.getenv("STRIPE_PUBLISHABLE_KEY")


def get_paypal_client_id() -> Optional[str]:
    return os.getenv("PAYPAL_CLIENT_ID")


def get_paypal_secret() -> Optional[str]:
    return os.getenv("PAYPAL_CLIENT_SECRET")


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
# Stripe stubs
# ---------------------------------------------------------------------------

def create_stripe_checkout_session(
    plan_id: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Stripe Checkout Session.

    TODO (when you have keys):
        import stripe
        stripe.api_key = get_stripe_secret_key()

        plan = PLANS[plan_id]
        if plan["type"] == "one_time":
            mode = "payment"
            line_items = [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": plan["name"]},
                    "unit_amount": int(plan["price_usd"] * 100),
                },
                "quantity": 1,
            }]
        else:
            mode = "subscription"
            # You must first create a Product + recurring Price in Stripe Dashboard
            # then put the price_id here, e.g. "price_xxxxx"
            line_items = [{"price": "price_YOUR_MONTHLY_PRICE_ID", "quantity": 1}]

        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=line_items,
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=customer_email,
        )
        return {"id": session.id, "url": session.url}

    For now this is a stub that returns a placeholder.
    """
    plan = PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"Unknown plan: {plan_id}")

    # Placeholder until real Stripe keys are connected
    return {
        "id": "cs_test_placeholder",
        "url": None,  # Real implementation returns session.url
        "message": (
            f"Stripe Checkout for '{plan['name']}' (${plan['price_usd']}) "
            "is not yet connected. Add your Stripe keys and implement the TODO above."
        ),
        "plan": plan,
    }


def verify_stripe_session(session_id: str) -> Dict[str, Any]:
    """
    After redirect from Stripe, verify the session was paid.

    TODO (when you have keys):
        import stripe
        stripe.api_key = get_stripe_secret_key()
        session = stripe.checkout.Session.retrieve(session_id)

        # Store plan_id in session metadata when creating the Checkout Session
        plan_id = None
        if session.metadata:
            plan_id = session.metadata.get("plan_id")

        return {
            "paid": session.payment_status == "paid",
            "customer_email": session.customer_details.email if session.customer_details else None,
            "mode": session.mode,                     # "payment" or "subscription"
            "subscription_id": session.subscription,
            "plan_id": plan_id,                       # "payg_100" or "monthly_75"
        }
    """
    return {
        "paid": False,
        "plan_id": None,
        "message": "Stripe verification not yet implemented. Connect your keys first.",
    }


# ---------------------------------------------------------------------------
# PayPal stubs (optional – can be added later)
# ---------------------------------------------------------------------------

def create_paypal_order(plan_id: str, return_url: str, cancel_url: str) -> Dict[str, Any]:
    """
    Create a PayPal order / subscription.

    TODO when ready:
        Use the PayPal REST API or the official SDK.
        For one-time: create an Order.
        For monthly: create a Subscription with a Billing Plan.
    """
    plan = PLANS.get(plan_id)
    return {
        "id": None,
        "approve_url": None,
        "message": (
            f"PayPal payment for '{plan['name'] if plan else plan_id}' "
            "is not yet connected. Add PayPal credentials later."
        ),
        "plan": plan,
    }


# ---------------------------------------------------------------------------
# Helper for the UI
# ---------------------------------------------------------------------------

def is_payments_configured() -> bool:
    """Quick check whether at least Stripe keys appear to be present."""
    return bool(get_stripe_secret_key() and get_stripe_publishable_key())

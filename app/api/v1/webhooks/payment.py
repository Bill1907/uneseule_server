"""
Payment gateway webhook handler.
Receives payment events from Stripe or Toss Payments.
"""

from fastapi import APIRouter, Request, HTTPException, status

from app.core.config import settings
from app.utils.webhook_validators import verify_stripe_signature


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/payment")
async def payment_webhook(request: Request):
    """
    Handle payment gateway webhooks (Stripe/Toss).

    Processes subscription payment events:
    - Payment succeeded
    - Payment failed
    - Subscription created/updated/cancelled

    Security:
        Verifies HMAC signature (provider-specific header)

    Returns:
        Status confirmation
    """
    # Get raw body for signature verification
    body = await request.body()

    # Determine provider and get signature
    if settings.PAYMENT_PROVIDER == "stripe":
        signature = request.headers.get("Stripe-Signature")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET or ""

        if not verify_stripe_signature(signature, body, webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Stripe webhook signature",
            )
    else:
        # Toss Payments signature verification
        # TODO: Implement Toss-specific signature verification
        pass

    # Parse webhook data
    data = await request.json()

    # TODO: Implement webhook processing
    # 1. Parse event type
    # 2. Update subscription status in database
    # 3. Send confirmation email to user
    # 4. Update usage limits if needed

    return {"status": "received", "message": "Payment webhook processing not yet implemented"}

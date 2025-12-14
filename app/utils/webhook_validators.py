"""
Webhook signature validation utilities.
Verify HMAC signatures from external services.
"""

import hashlib
import hmac
from typing import Optional


def verify_webhook_signature(
    signature: Optional[str],
    payload: bytes,
    secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 signature for webhook payload.

    Args:
        signature: Signature from webhook header
        payload: Raw webhook payload (bytes)
        secret: Webhook secret key

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        return False

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(signature, expected_signature)


def verify_elevenlabs_signature(
    signature: Optional[str],
    payload: bytes,
    secret: str,
) -> bool:
    """
    Verify ElevenLabs webhook signature.

    Args:
        signature: ElevenLabs-Signature header value
        payload: Raw webhook payload
        secret: ElevenLabs webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    return verify_webhook_signature(signature, payload, secret)


def verify_stripe_signature(
    signature: Optional[str],
    payload: bytes,
    secret: str,
) -> bool:
    """
    Verify Stripe webhook signature.

    Args:
        signature: Stripe-Signature header value
        payload: Raw webhook payload
        secret: Stripe webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    # Stripe uses a different signature format: t=timestamp,v1=signature
    # This is a simplified version
    if not signature:
        return False

    parts = dict(part.split("=") for part in signature.split(","))
    stripe_signature = parts.get("v1")

    if not stripe_signature:
        return False

    return verify_webhook_signature(stripe_signature, payload, secret)

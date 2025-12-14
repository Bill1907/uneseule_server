"""
ElevenLabs webhook handler.
Receives conversation data after voice calls.
"""

from fastapi import APIRouter, Request, HTTPException, status

from app.core.config import settings
from app.utils.webhook_validators import verify_elevenlabs_signature


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/elevenlabs")
async def elevenlabs_webhook(request: Request):
    """
    Handle ElevenLabs post-call webhook.

    Receives conversation transcripts and analysis after voice calls complete.

    Security:
        Verifies HMAC signature in ElevenLabs-Signature header

    Request body example:
        {
            "type": "post_call_transcription",
            "event_timestamp": 1234567890,
            "data": {
                "conversation_id": "uuid",
                "child_id": "uuid",
                "transcript": [...],
                "analysis": {...}
            }
        }

    Returns:
        Status confirmation
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("ElevenLabs-Signature")

    # Verify signature
    # TODO: Get actual webhook secret from settings
    webhook_secret = getattr(settings, "ELEVENLABS_WEBHOOK_SECRET", "")

    if not verify_elevenlabs_signature(signature, body, webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse webhook data
    data = await request.json()

    # TODO: Implement webhook processing
    # 1. Extract conversation data
    # 2. Store in MongoDB
    # 3. Update child personality traits
    # 4. Trigger GraphQL subscription for parent app
    # 5. Send notification

    return {"status": "received", "message": "Webhook processing not yet implemented"}

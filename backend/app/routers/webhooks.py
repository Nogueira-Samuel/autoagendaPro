"""
Webhooks Router

Receives webhooks from external services:
- Evolution API WhatsApp messages
- Future: Google Calendar events
"""

import hmac
import hashlib
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Tenant
from app.schemas.webhook import WhatsAppWebhookEvent
from app.services import ConversationManager, EvolutionAPIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_webhook_signature(
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
) -> None:
    """
    Verify webhook request comes from Evolution API.

    Validates the webhook signature to prevent unauthorized access.

    Args:
        x_webhook_signature: HMAC signature from webhook request

    Raises:
        HTTPException: 401 if signature is invalid or missing
    """
    if not x_webhook_signature:
        logger.warning("Webhook request missing signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )

    # In production, validate the signature against a secret key
    # For now, we check if the signature exists
    # TODO: Implement proper HMAC signature validation when Evolution API provides it
    if len(x_webhook_signature) < 10:
        logger.warning(f"Invalid webhook signature: {x_webhook_signature[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


def sanitize_message_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize and validate message text.

    Args:
        text: Raw message text
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        ValueError: If text is too long or contains invalid characters
    """
    if not text:
        return ""

    # Truncate to maximum length
    if len(text) > max_length:
        logger.warning(f"Message text truncated from {len(text)} to {max_length} chars")
        text = text[:max_length]

    # Remove null bytes and other problematic characters
    text = text.replace('\x00', '').strip()

    return text


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def whatsapp_webhook(
    event: WhatsAppWebhookEvent,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_webhook_signature),
) -> dict[str, str]:
    """
    Receive WhatsApp messages from Evolution API.

    Process flow:
    1. Extract phone number and message from webhook event
    2. Identify tenant by instance name
    3. Process message with ConversationManager (LLM + intent detection)
    4. Send response back via WhatsApp

    Args:
        event: WhatsApp webhook event from Evolution API
        db: Database session

    Returns:
        {"status": "processed"}

    Raises:
        HTTPException: 404 if tenant not found
        HTTPException: 500 if processing fails
    """
    try:
        # Extract message data from Evolution API webhook
        instance_name = event.instance

        # Extract phone number (remove @s.whatsapp.net suffix)
        remote_jid = event.data.data.key.remoteJid
        phone = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

        # Extract message text (handle different message types safely)
        message_data = event.data.data.message
        message_text = ""

        try:
            # Try to get conversation text first
            if hasattr(message_data, "conversation") and message_data.conversation:
                message_text = message_data.conversation
            # Try extended text message
            elif hasattr(message_data, "extendedTextMessage"):
                extended = getattr(message_data, "extendedTextMessage", None)
                if extended and hasattr(extended, "text"):
                    message_text = extended.text
        except (AttributeError, TypeError) as e:
            logger.warning(f"Error extracting message text: {e}")

        if not message_text:
            logger.warning(
                f"Received webhook with no text message: instance={instance_name}, "
                f"phone={phone}"
            )
            return {"status": "ignored"}

        # Sanitize message text
        try:
            message_text = sanitize_message_text(message_text)
        except Exception as e:
            logger.error(f"Error sanitizing message: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message format",
            )

        logger.info(
            f"Received WhatsApp message: instance={instance_name}, "
            f"phone={phone}, message_length={len(message_text)}"
        )

        # Find tenant by instance name
        result = await db.execute(
            select(Tenant).where(Tenant.evolution_instance_name == instance_name)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.error(f"Tenant not found for instance: {instance_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant not found for instance: {instance_name}",
            )

        # Process message with ConversationManager
        manager = ConversationManager()
        response_data = await manager.process_message(
            tenant_id=tenant.id,
            customer_phone=phone,
            message=message_text,
            db=db,
        )

        logger.info(
            f"Message processed: tenant_id={tenant.id}, phone={phone}, "
            f"intent={response_data.get('intent')}"
        )

        # Send response via WhatsApp
        async with await EvolutionAPIService.create_from_tenant(tenant) as whatsapp:
            # Send typing indicator for natural feel
            await whatsapp.send_typing(phone, duration_seconds=2)

            # Send response
            whatsapp_response = await whatsapp.send_text(
                phone=phone,
                message=response_data["response"],
            )

            if not whatsapp_response.success:
                logger.error(
                    f"Failed to send WhatsApp response: {whatsapp_response.error}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send WhatsApp response",
                )

        logger.info(
            f"Response sent: tenant_id={tenant.id}, phone={phone}, "
            f"message_id={whatsapp_response.message_id}"
        )

        return {"status": "processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )


@router.post("/whatsapp/status", status_code=status.HTTP_200_OK)
async def whatsapp_status_webhook(
    event: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_webhook_signature),
) -> dict[str, str]:
    """
    Receive WhatsApp status updates from Evolution API.

    Status events include:
    - Message sent/delivered/read
    - Connection status changes
    - QR code updates

    Args:
        event: Status event from Evolution API
        db: Database session

    Returns:
        {"status": "received"}
    """
    try:
        instance_name = event.get("instance")
        event_type = event.get("event")

        logger.info(
            f"Received WhatsApp status: instance={instance_name}, "
            f"event={event_type}"
        )

        # TODO: Handle different status events
        # - Update message delivery status
        # - Handle connection changes
        # - Log QR code updates

        return {"status": "received"}

    except Exception as e:
        logger.exception(f"Error processing status webhook: {e}")
        # Don't raise exception - status webhooks are not critical
        return {"status": "error", "message": str(e)}


@router.get("/health", status_code=status.HTTP_200_OK)
async def webhook_health() -> dict[str, str]:
    """
    Health check endpoint for webhook service.

    Returns:
        {"status": "healthy"}
    """
    return {"status": "healthy"}

"""
Webhooks Router

Receives webhooks from external services:
- Evolution API WhatsApp messages
- Future: Google Calendar events
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Tenant
from app.schemas.webhook import WhatsAppWebhookEvent
from app.services import ConversationManager, EvolutionAPIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def whatsapp_webhook(
    event: WhatsAppWebhookEvent,
    db: AsyncSession = Depends(get_db),
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

        # Extract message text (handle different message types)
        message_data = event.data.data.message
        message_text = (
            message_data.conversation
            or message_data.extendedTextMessage.text
            if hasattr(message_data, "extendedTextMessage")
            else ""
        )

        if not message_text:
            logger.warning(
                f"Received webhook with no text message: instance={instance_name}, "
                f"phone={phone}"
            )
            return {"status": "ignored"}

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

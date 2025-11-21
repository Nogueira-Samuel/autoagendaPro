"""
Notifications Router

Endpoints for managing and viewing notification logs.

Endpoints:
- GET /notifications - List all notifications for tenant
- GET /notifications/stats - Get notification statistics
- POST /notifications/test/confirmation/{appointment_id} - Test confirmation notification
- POST /notifications/test/reminder/{appointment_id} - Test reminder notification
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.notification_log import NotificationLog
from app.models.appointment import Appointment
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    """Response model for notification log"""
    id: int
    appointment_id: Optional[int]
    recipient_type: str
    recipient_phone: str
    notification_type: str
    message_text: str
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Statistics for notifications"""
    total: int
    sent: int
    failed: int
    pending: int
    success_rate: float


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all notifications for the current tenant.

    Filter by status and notification type.
    """
    query = select(NotificationLog).where(
        NotificationLog.tenant_id == current_user.tenant_id
    )

    if status_filter:
        query = query.where(NotificationLog.status == status_filter)

    if notification_type:
        query = query.where(NotificationLog.notification_type == notification_type)

    query = query.order_by(NotificationLog.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    notifications = result.scalars().all()

    return notifications


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification statistics for the current tenant.

    Returns counts and success rate for the specified number of days.
    """
    since = datetime.now() - timedelta(days=days)

    # Get all notifications in the period
    query = select(NotificationLog).where(
        NotificationLog.tenant_id == current_user.tenant_id,
        NotificationLog.created_at >= since
    )

    result = await db.execute(query)
    all_notifications = result.scalars().all()

    total = len(all_notifications)
    sent = sum(1 for n in all_notifications if n.status == 'sent')
    failed = sum(1 for n in all_notifications if n.status == 'failed')
    pending = sum(1 for n in all_notifications if n.status == 'pending')

    success_rate = (sent / total * 100) if total > 0 else 0

    return NotificationStats(
        total=total,
        sent=sent,
        failed=failed,
        pending=pending,
        success_rate=round(success_rate, 2)
    )


@router.post("/test/confirmation/{appointment_id}")
async def test_confirmation(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test sending a confirmation notification for an appointment.

    Useful for testing the notification system.
    """
    # Get appointment
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Create notification service (note: it uses sync Session internally)
    # We'll need to get a sync session for this
    from app.database import SessionLocal
    sync_db = SessionLocal()
    try:
        notification_service = NotificationService(sync_db)
        success = await notification_service.send_confirmation(appointment)
        sync_db.close()
    except Exception as e:
        sync_db.close()
        logger.error(f"Error sending test confirmation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

    return {
        "success": success,
        "message": "Test notification sent" if success else "Failed to send notification"
    }


@router.post("/test/reminder/{appointment_id}")
async def test_reminder(
    appointment_id: int,
    reminder_type: str = Query(default="24h", regex="^(24h|1h)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test sending a reminder notification for an appointment.

    Args:
        appointment_id: ID of the appointment
        reminder_type: Type of reminder (24h or 1h)
    """
    # Get appointment
    query = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    # Create notification service with sync session
    from app.database import SessionLocal
    sync_db = SessionLocal()
    try:
        notification_service = NotificationService(sync_db)

        if reminder_type == "24h":
            success = await notification_service.send_reminder_24h(appointment)
        else:
            success = await notification_service.send_reminder_1h(appointment)

        sync_db.close()
    except Exception as e:
        sync_db.close()
        logger.error(f"Error sending test reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reminder: {str(e)}"
        )

    return {
        "success": success,
        "reminder_type": reminder_type,
        "message": f"Test {reminder_type} reminder sent" if success else "Failed to send reminder"
    }

"""
Appointments Router

CRUD endpoints for appointment management.

All endpoints are multi-tenant aware and require authentication.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Appointment, User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    tenant_id: int = Query(..., description="Tenant ID for multi-tenant filtering"),
    start_date: date | None = Query(None, description="Filter by start date (inclusive)"),
    end_date: date | None = Query(None, description="Filter by end date (inclusive)"),
    status: str | None = Query(None, description="Filter by status"),
    customer_id: int | None = Query(None, description="Filter by customer ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=settings.MIN_PAGE_SIZE, le=settings.MAX_PAGE_SIZE, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Appointment]:
    """
    List appointments with filters and pagination.

    Query parameters:
    - tenant_id: Required - filter by tenant
    - start_date: Optional - filter appointments from this date
    - end_date: Optional - filter appointments until this date
    - status: Optional - filter by status (pending, confirmed, cancelled, etc)
    - customer_id: Optional - filter by customer
    - skip: Pagination offset (default: 0)
    - limit: Pagination limit (default: 100, max: 500)

    Returns:
        List of appointments matching filters
    """
    # Validate tenant access - users can only access their own tenant
    if current_user.tenant_id != tenant_id:
        logger.warning(
            f"Unauthorized tenant access attempt: user_tenant={current_user.tenant_id}, "
            f"requested_tenant={tenant_id}, user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tenant's data",
        )

    # Build query with filters
    query = select(Appointment).where(Appointment.tenant_id == tenant_id)

    if start_date:
        query = query.where(Appointment.scheduled_date >= start_date)

    if end_date:
        query = query.where(Appointment.scheduled_date <= end_date)

    if status:
        query = query.where(Appointment.status == status)

    if customer_id:
        query = query.where(Appointment.customer_id == customer_id)

    # Order by date and time
    query = query.order_by(
        Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc()
    )

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    appointments = result.scalars().all()

    logger.info(
        f"Listed appointments: tenant_id={tenant_id}, count={len(appointments)}, "
        f"filters=(start_date={start_date}, end_date={end_date}, status={status})"
    )

    return list(appointments)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Appointment:
    """
    Get appointment by ID.

    Args:
        appointment_id: Appointment ID

    Returns:
        Appointment details

    Raises:
        HTTPException: 404 if appointment not found
    """
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        logger.warning(f"Appointment not found: id={appointment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} not found",
        )

    # Validate tenant access
    if appointment.tenant_id != current_user.tenant_id:
        logger.warning(
            f"Unauthorized access attempt: user_tenant={current_user.tenant_id}, "
            f"appointment_tenant={appointment.tenant_id}, user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tenant's data",
        )

    logger.info(f"Retrieved appointment: id={appointment_id}")

    return appointment


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Appointment:
    """
    Create new appointment.

    Args:
        appointment_data: Appointment details

    Returns:
        Created appointment

    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        # Validate tenant access
        if appointment_data.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized tenant creation attempt: user_tenant={current_user.tenant_id}, "
                f"data_tenant={appointment_data.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only create appointments for your own tenant",
            )

        # Create appointment model
        appointment = Appointment(**appointment_data.model_dump())
        db.add(appointment)
        await db.flush()  # Get appointment ID before commit

        # Commit transaction
        await db.commit()
        await db.refresh(appointment)

        logger.info(
            f"Created appointment: id={appointment.id}, tenant_id={appointment.tenant_id}"
        )

        return appointment

    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create appointment: {str(e)}",
        )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Appointment:
    """
    Update appointment.

    Args:
        appointment_id: Appointment ID
        appointment_data: Updated appointment data

    Returns:
        Updated appointment

    Raises:
        HTTPException: 404 if appointment not found
        HTTPException: 400 if update fails
    """
    try:
        # Get appointment
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        # Validate tenant access
        if appointment.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized update attempt: user_tenant={current_user.tenant_id}, "
                f"appointment_tenant={appointment.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update your own tenant's appointments",
            )

        # Update fields
        update_data = appointment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)

        # Commit transaction
        await db.commit()
        await db.refresh(appointment)

        logger.info(f"Updated appointment: id={appointment_id}")

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update appointment: {str(e)}",
        )


@router.delete("/{appointment_id}", status_code=status.HTTP_200_OK)
async def cancel_appointment(
    appointment_id: int,
    cancellation_reason: str | None = Query(None, description="Reason for cancellation"),
    cancelled_by: str = Query("customer", description="Who cancelled (customer/business)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Cancel appointment.

    Args:
        appointment_id: Appointment ID
        cancellation_reason: Optional reason for cancellation
        cancelled_by: Who cancelled (customer or business)

    Returns:
        {"status": "cancelled", "appointment_id": ...}

    Raises:
        HTTPException: 404 if appointment not found
    """
    try:
        # Get appointment
        result = await db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        # Validate tenant access
        if appointment.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized cancel attempt: user_tenant={current_user.tenant_id}, "
                f"appointment_tenant={appointment.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only cancel your own tenant's appointments",
            )

        # Use model method to cancel
        from app.models.appointment import CancelledBy

        cancelled_by_enum = (
            CancelledBy.BUSINESS if cancelled_by == "business" else CancelledBy.CUSTOMER
        )
        appointment.cancel(reason=cancellation_reason, cancelled_by=cancelled_by_enum)

        # Commit transaction
        await db.commit()

        logger.info(
            f"Cancelled appointment: id={appointment_id}, reason={cancellation_reason}"
        )

        return {
            "status": "cancelled",
            "appointment_id": appointment_id,
            "cancelled_by": cancelled_by,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error cancelling appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel appointment: {str(e)}",
        )

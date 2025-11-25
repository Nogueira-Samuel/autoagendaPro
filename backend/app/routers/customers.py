"""
Customers Router

CRUD endpoints for customer management.

All endpoints are multi-tenant aware and require authentication.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Customer, Appointment, User
from app.models.appointment import AppointmentStatus
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    tenant_id: int = Query(..., description="Tenant ID for multi-tenant filtering"),
    search: str | None = Query(None, description="Search by name or phone"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Customer]:
    """
    List customers with filters and pagination.

    Query parameters:
    - tenant_id: Required - filter by tenant
    - search: Optional - search by name or phone (partial match)
    - skip: Pagination offset (default: 0)
    - limit: Pagination limit (default: 100, max: 500)

    Returns:
        List of customers matching filters
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
    query = select(Customer).where(Customer.tenant_id == tenant_id)

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Customer.name.ilike(search_pattern))
            | (Customer.phone.ilike(search_pattern))
            | (Customer.email.ilike(search_pattern))
        )

    # Order by name
    query = query.order_by(Customer.name)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()

    logger.info(
        f"Listed customers: tenant_id={tenant_id}, count={len(customers)}, "
        f"search={search}"
    )

    return list(customers)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    """
    Get customer by ID.

    Args:
        customer_id: Customer ID

    Returns:
        Customer details

    Raises:
        HTTPException: 404 if customer not found
    """
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        logger.warning(f"Customer not found: id={customer_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )

    # Validate tenant access
    if customer.tenant_id != current_user.tenant_id:
        logger.warning(
            f"Unauthorized access attempt: user_tenant={current_user.tenant_id}, "
            f"customer_tenant={customer.tenant_id}, user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tenant's data",
        )

    logger.info(f"Retrieved customer: id={customer_id}")

    return customer


@router.get("/{customer_id}/appointments")
async def get_customer_appointments(
    customer_id: int,
    include_cancelled: bool = Query(False, description="Include cancelled appointments"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get all appointments for a customer.

    Args:
        customer_id: Customer ID
        include_cancelled: Whether to include cancelled appointments
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        {
            "customer_id": int,
            "total_appointments": int,
            "appointments": [...]
        }

    Raises:
        HTTPException: 404 if customer not found
    """
    # Check customer exists
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )

    # Validate tenant access
    if customer.tenant_id != current_user.tenant_id:
        logger.warning(
            f"Unauthorized access attempt: user_tenant={current_user.tenant_id}, "
            f"customer_tenant={customer.tenant_id}, user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tenant's data",
        )

    # Build query
    query = select(Appointment).where(Appointment.customer_id == customer_id)

    if not include_cancelled:
        query = query.where(Appointment.status != AppointmentStatus.CANCELLED)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_appointments = total_result.scalar()

    # Get appointments with pagination
    query = query.order_by(
        Appointment.scheduled_date.desc(), Appointment.scheduled_time.desc()
    )
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    appointments = result.scalars().all()

    logger.info(
        f"Retrieved customer appointments: customer_id={customer_id}, "
        f"count={len(appointments)}, total={total_appointments}"
    )

    return {
        "customer_id": customer_id,
        "total_appointments": total_appointments,
        "appointments": appointments,
    }


@router.get("/phone/{phone}", response_model=CustomerResponse)
async def get_customer_by_phone(
    phone: str,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    """
    Get customer by phone number.

    Useful for webhook processing and WhatsApp integration.

    Args:
        phone: Phone number (Brazilian format: 5521999999999)
        tenant_id: Tenant ID

    Returns:
        Customer details

    Raises:
        HTTPException: 404 if customer not found
    """
    # Validate tenant access
    if current_user.tenant_id != tenant_id:
        logger.warning(
            f"Unauthorized tenant access attempt: user_tenant={current_user.tenant_id}, "
            f"requested_tenant={tenant_id}, user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own tenant's data",
        )

    # Clean phone number
    phone_clean = "".join(filter(str.isdigit, phone))

    result = await db.execute(
        select(Customer).where(
            Customer.phone == phone_clean, Customer.tenant_id == tenant_id
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        logger.warning(f"Customer not found by phone: phone={phone}, tenant_id={tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with phone {phone} not found",
        )

    logger.info(f"Retrieved customer by phone: id={customer.id}, phone={phone}")

    return customer


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    """
    Create new customer.

    Args:
        customer_data: Customer details

    Returns:
        Created customer

    Raises:
        HTTPException: 400 if customer with phone already exists
    """
    try:
        # Validate tenant access
        if customer_data.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized tenant creation attempt: user_tenant={current_user.tenant_id}, "
                f"data_tenant={customer_data.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only create customers for your own tenant",
            )

        # Check if customer with phone already exists for this tenant
        phone_clean = "".join(filter(str.isdigit, customer_data.phone))

        result = await db.execute(
            select(Customer).where(
                Customer.phone == phone_clean,
                Customer.tenant_id == customer_data.tenant_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.warning(
                f"Customer with phone already exists: phone={phone_clean}, "
                f"tenant_id={customer_data.tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with phone {customer_data.phone} already exists",
            )

        # Create customer
        customer = Customer(**customer_data.model_dump())
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        logger.info(
            f"Created customer: id={customer.id}, phone={customer.phone}, "
            f"tenant_id={customer.tenant_id}"
        )

        return customer

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create customer: {str(e)}",
        )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Customer:
    """
    Update customer.

    Args:
        customer_id: Customer ID
        customer_data: Updated customer data

    Returns:
        Updated customer

    Raises:
        HTTPException: 404 if customer not found
        HTTPException: 400 if update fails
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )

        # Validate tenant access
        if customer.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized update attempt: user_tenant={current_user.tenant_id}, "
                f"customer_tenant={customer.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update your own tenant's customers",
            )

        # Update fields
        update_data = customer_data.model_dump(exclude_unset=True)

        # If updating phone, check for duplicates
        if "phone" in update_data:
            phone_clean = "".join(filter(str.isdigit, update_data["phone"]))

            result = await db.execute(
                select(Customer).where(
                    Customer.phone == phone_clean,
                    Customer.tenant_id == customer.tenant_id,
                    Customer.id != customer_id,  # Exclude current customer
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer with phone {update_data['phone']} already exists",
                )

        # Apply updates
        for field, value in update_data.items():
            setattr(customer, field, value)

        # Commit transaction
        await db.commit()
        await db.refresh(customer)

        logger.info(f"Updated customer: id={customer_id}")

        return customer

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update customer: {str(e)}",
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete customer.

    Note: This will cascade delete all associated appointments and conversations.
    Use with caution!

    Args:
        customer_id: Customer ID

    Raises:
        HTTPException: 404 if customer not found
        HTTPException: 400 if customer has active appointments
    """
    try:
        # Get customer
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )

        # Validate tenant access
        if customer.tenant_id != current_user.tenant_id:
            logger.warning(
                f"Unauthorized delete attempt: user_tenant={current_user.tenant_id}, "
                f"customer_tenant={customer.tenant_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only delete your own tenant's customers",
            )

        # Check for active appointments
        result = await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.customer_id == customer_id,
                Appointment.status.in_(["pending", "confirmed"]),
            )
        )
        active_appointments = result.scalar()

        if active_appointments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete customer with {active_appointments} active appointments. "
                "Cancel appointments first.",
            )

        # Delete customer
        await db.delete(customer)
        await db.commit()

        logger.info(f"Deleted customer: id={customer_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete customer: {str(e)}",
        )

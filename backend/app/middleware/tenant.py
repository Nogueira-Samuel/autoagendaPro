"""
Tenant Identification Middleware

Extracts and validates tenant from requests for multi-tenant isolation.

Supports multiple tenant identification methods:
1. Query parameter: ?tenant_id=1
2. HTTP header: X-Tenant-ID: 1
3. Subdomain: tenant1.autoagenda.com (future)
"""

import logging

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant

logger = logging.getLogger(__name__)


async def get_tenant_from_request(
    request: Request,
    db: AsyncSession,
) -> Tenant:
    """
    Extract and validate tenant from request.

    Priority order:
    1. Query parameter: ?tenant_id=1
    2. HTTP header: X-Tenant-ID
    3. Subdomain parsing (future implementation)

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Tenant model instance

    Raises:
        HTTPException: 400 if tenant ID not provided
        HTTPException: 404 if tenant not found
        HTTPException: 403 if tenant is inactive

    Example:
        # In a route
        @router.get("/protected")
        async def protected_route(
            request: Request,
            db: AsyncSession = Depends(get_db)
        ):
            tenant = await get_tenant_from_request(request, db)
            return {"tenant_id": tenant.id}
    """
    tenant_id: int | None = None

    # Method 1: Query parameter
    if "tenant_id" in request.query_params:
        try:
            tenant_id = int(request.query_params["tenant_id"])
            logger.debug(f"Tenant ID from query param: {tenant_id}")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant_id format. Must be an integer.",
            )

    # Method 2: HTTP header
    elif "X-Tenant-ID" in request.headers:
        try:
            tenant_id = int(request.headers["X-Tenant-ID"])
            logger.debug(f"Tenant ID from header: {tenant_id}")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Tenant-ID header format. Must be an integer.",
            )

    # Method 3: Subdomain (future implementation)
    # elif request.url.hostname:
    #     # Parse subdomain from hostname
    #     hostname = request.url.hostname
    #     parts = hostname.split('.')
    #
    #     if len(parts) >= 3:  # subdomain.domain.tld
    #         subdomain = parts[0]
    #
    #         # Query tenant by slug
    #         result = await db.execute(
    #             select(Tenant).where(Tenant.slug == subdomain)
    #         )
    #         tenant = result.scalar_one_or_none()
    #
    #         if tenant:
    #             logger.debug(f"Tenant ID from subdomain: {tenant.id}")
    #             return tenant

    # No tenant identification method worked
    if not tenant_id:
        logger.warning(f"Tenant ID not provided: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID required. Provide via ?tenant_id=1 or X-Tenant-ID header.",
        )

    # Query tenant from database
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        logger.warning(f"Tenant not found: id={tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )

    # Check if tenant is active
    if not tenant.is_active:
        logger.warning(f"Inactive tenant access attempt: id={tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant {tenant_id} is inactive",
        )

    logger.debug(
        f"Tenant validated: id={tenant.id}, name={tenant.name}, plan={tenant.plan}"
    )

    return tenant


async def get_tenant_from_slug(
    slug: str,
    db: AsyncSession,
) -> Tenant:
    """
    Get tenant by slug.

    Args:
        slug: Tenant slug (URL-friendly identifier)
        db: Database session

    Returns:
        Tenant model instance

    Raises:
        HTTPException: 404 if tenant not found or inactive

    Example:
        >>> tenant = await get_tenant_from_slug("my-business", db)
        >>> print(tenant.name)
        'My Business'
    """
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()

    if not tenant:
        logger.warning(f"Tenant not found by slug: {slug}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with slug '{slug}' not found",
        )

    if not tenant.is_active:
        logger.warning(f"Inactive tenant access via slug: {slug}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{slug}' is inactive",
        )

    return tenant


def validate_tenant_access(user_tenant_id: int, resource_tenant_id: int) -> None:
    """
    Validate that user can access resource (same tenant).

    Prevents cross-tenant data access.

    Args:
        user_tenant_id: User's tenant ID
        resource_tenant_id: Resource's tenant ID

    Raises:
        HTTPException: 403 if tenant mismatch

    Example:
        # In a route
        user = await get_current_user(...)
        appointment = await get_appointment(...)
        validate_tenant_access(user.tenant_id, appointment.tenant_id)
    """
    if user_tenant_id != resource_tenant_id:
        logger.warning(
            f"Cross-tenant access attempt: user_tenant={user_tenant_id}, "
            f"resource_tenant={resource_tenant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Resource belongs to different tenant.",
        )

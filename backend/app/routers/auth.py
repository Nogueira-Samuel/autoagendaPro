"""
Authentication Router

Basic authentication endpoints.

NOTE: This is a basic implementation. Full JWT authentication with password
hashing will be implemented in Prompt 8 (Utils).

Current endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login (returns placeholder token)
- GET /auth/me - Get current user (placeholder)
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserLogin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register new user.

    Creates a new user account for the specified tenant.

    NOTE: Password hashing will be implemented in Prompt 8 (Utils).
    Currently stores placeholder password hash.

    Args:
        user_data: User registration data

    Returns:
        Created user (without password)

    Raises:
        HTTPException: 400 if email already registered for this tenant
    """
    try:
        # Check if email already exists for this tenant
        result = await db.execute(
            select(User).where(
                User.email == user_data.email,
                User.tenant_id == user_data.tenant_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.warning(
                f"Registration failed - email exists: email={user_data.email}, "
                f"tenant_id={user_data.tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered for this tenant",
            )

        # Create user
        # TODO: Hash password in Prompt 8
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
            password_hash="TODO_HASH_PASSWORD",  # Will be hashed in Prompt 8
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(
            f"User registered: id={user.id}, email={user.email}, "
            f"tenant_id={user.tenant_id}"
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register user: {str(e)}",
        )


@router.post("/login")
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Login user.

    Authenticates user and returns JWT access token.

    NOTE: This is a placeholder. JWT token generation and password verification
    will be implemented in Prompt 8 (Utils).

    Args:
        login_data: Login credentials (email, password, tenant_id)

    Returns:
        {
            "access_token": "jwt_token_here",
            "token_type": "bearer",
            "user": {...}
        }

    Raises:
        HTTPException: 401 if credentials invalid
    """
    try:
        # Find user by email and tenant
        result = await db.execute(
            select(User).where(
                User.email == login_data.email,
                User.tenant_id == login_data.tenant_id,
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(
                f"Login failed - user not found: email={login_data.email}, "
                f"tenant_id={login_data.tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed - user inactive: id={user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        # TODO: Verify password in Prompt 8
        # For now, accept any password (INSECURE - will be fixed)

        logger.info(f"User logged in: id={user.id}, email={user.email}")

        # TODO: Generate JWT token in Prompt 8
        return {
            "access_token": "TODO_JWT_TOKEN",  # Will be generated in Prompt 8
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_id": user.tenant_id,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    # TODO: Add JWT token dependency in Prompt 8
) -> User:
    """
    Get current user information.

    Requires valid JWT token in Authorization header.

    NOTE: This is a placeholder. JWT token validation will be implemented
    in Prompt 8 (Utils).

    Returns:
        Current user details

    Raises:
        HTTPException: 401 if not authenticated
    """
    # TODO: Extract user from JWT token in Prompt 8
    # For now, return placeholder error

    logger.warning("get_current_user_info called but JWT not implemented")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="JWT authentication not yet implemented. Will be added in Prompt 8.",
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """
    Logout user.

    For JWT-based auth, logout is typically client-side (delete token).
    This endpoint is here for API completeness.

    Returns:
        {"message": "Successfully logged out"}
    """
    logger.info("User logged out (client-side)")

    return {"message": "Successfully logged out"}


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Refresh access token.

    Uses refresh token to generate new access token.

    NOTE: This is a placeholder. Refresh token logic will be implemented
    in Prompt 8 (Utils).

    Args:
        refresh_token: Refresh token

    Returns:
        {
            "access_token": "new_jwt_token",
            "token_type": "bearer"
        }

    Raises:
        HTTPException: 401 if refresh token invalid
    """
    # TODO: Implement refresh token logic in Prompt 8

    logger.warning("refresh_token called but not implemented")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not yet implemented. Will be added in Prompt 8.",
    )

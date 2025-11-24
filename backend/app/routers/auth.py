"""
Authentication Router

JWT-based authentication endpoints with bcrypt password hashing.

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login (returns JWT token)
- GET /auth/me - Get current user from JWT
- POST /auth/logout - Logout (client-side)
- POST /auth/refresh - Refresh JWT token
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    get_current_user,
)

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
    Password is hashed using bcrypt before storage.

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

        # Create user with hashed password
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
            password_hash=get_password_hash(user_data.password),
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

    Authenticates user with email/password and returns JWT access token.
    Password is verified using bcrypt.

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

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(
                f"Login failed - invalid password: email={login_data.email}"
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

        # Update last login timestamp
        from datetime import datetime
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        # Generate JWT access token
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role,
            }
        )

        # Generate refresh token
        refresh_token = create_refresh_token(
            data={
                "user_id": user.id,
                "email": user.email,
            }
        )

        logger.info(f"User logged in: id={user.id}, email={user.email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
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
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user information.

    Requires valid JWT token in Authorization header.
    Token is validated and user is retrieved from database.

    Returns:
        Current user details

    Raises:
        HTTPException: 401 if not authenticated or token invalid

    Example:
        # Request
        GET /api/v1/auth/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        # Response
        {
            "id": 1,
            "email": "user@example.com",
            "full_name": "John Doe",
            "role": "admin",
            "tenant_id": 1,
            ...
        }
    """
    logger.debug(f"Current user info requested: id={current_user.id}")

    return current_user


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
async def refresh_token_endpoint(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Refresh access token.

    Uses refresh token to generate new access token.
    Refresh tokens have longer expiration than access tokens.

    Args:
        refresh_token: Refresh token from login response

    Returns:
        {
            "access_token": "new_jwt_token",
            "token_type": "bearer"
        }

    Raises:
        HTTPException: 401 if refresh token invalid or expired
    """
    try:
        # Verify refresh token
        payload = verify_access_token(refresh_token)

        # Check token type
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Extract user_id
        user_id: int = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new access token
        new_access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "role": user.role,
            }
        )

        logger.info(f"Access token refreshed: user_id={user.id}")

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token",
        )

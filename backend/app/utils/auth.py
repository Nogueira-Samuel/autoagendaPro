"""
Authentication Utilities

JWT token generation/validation and password hashing for AutoAgenda Pro.

Uses:
- python-jose for JWT
- passlib with bcrypt for password hashing
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt.

    Bcrypt has a 72-byte limit, so we truncate the password
    to ensure compatibility with all inputs.
    """
    # 1. Transforma a string em bytes
    password_bytes = password.encode('utf-8')

    # 2. Corta (fatia) para pegar apenas os primeiros 72 bytes
    # Isso garente que nunca estoure o limite
    password_bytes_truncate = password_bytes[:72]

    # 3. Trasnforma de volta para string, ignorando erros se cortar um caractere no meio
    password_truncate = password_bytes_truncate.decode('utf-8', errors='ignore')

    # 4. Gera o hash com a senhra segura cortada
    return pwd_context.hash(password_truncate)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        plain_password: Plain text password from login attempt
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT access token.

    Payload typically includes:
    - user_id: User ID
    - email: User email
    - tenant_id: Tenant ID (for multi-tenant)
    - role: User role

    Args:
        data: Token payload (claims)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(
        ...     data={"user_id": 1, "email": "user@example.com", "tenant_id": 1}
        ... )
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add expiration to payload
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.API_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.debug(f"Created access token for user_id={data.get('user_id')}")

    return encoded_jwt


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Verify and decode JWT access token.

    Validates:
    - Token signature
    - Token expiration
    - Algorithm match

    Args:
        token: JWT token string

    Returns:
        Decoded token payload (claims)

    Raises:
        HTTPException: If token is invalid, expired, or malformed

    Example:
        >>> token = create_access_token({"user_id": 1})
        >>> payload = verify_access_token(token)
        >>> print(payload["user_id"])
        1
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.API_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # Validate required fields
        user_id: int | None = payload.get("user_id")
        if user_id is None:
            logger.warning("Token missing user_id claim")
            raise credentials_exception

        logger.debug(f"Token verified for user_id={user_id}")

        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    FastAPI dependency for protected routes. Extracts Bearer token
    from Authorization header, validates it, and returns User model.

    Usage:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"user_id": current_user.id, "email": current_user.email}

    Args:
        credentials: HTTP Bearer credentials (auto-injected by FastAPI)
        db: Database session (auto-injected)

    Returns:
        User model instance of authenticated user

    Raises:
        HTTPException: 401 if token invalid or user not found
        HTTPException: 403 if user is inactive
    """
    # Extract token from Bearer scheme
    token = credentials.credentials

    # Verify and decode token
    payload = verify_access_token(token)

    # Extract user_id from payload
    user_id: int = payload.get("user_id")
    if user_id is None:
        logger.warning("Token payload missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Query user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"User not found: id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    logger.debug(f"User authenticated: id={user.id}, email={user.email}")

    return user


async def get_current_active_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify super_admin role.

    FastAPI dependency for admin-only routes.

    Usage:
        @router.delete("/admin/delete-tenant/{tenant_id}")
        async def delete_tenant(
            tenant_id: int,
            admin: User = Depends(get_current_active_superadmin)
        ):
            # Only super_admin can access this

    Args:
        current_user: Current authenticated user

    Returns:
        User model instance (guaranteed to be super_admin)

    Raises:
        HTTPException: 403 if user is not super_admin
    """
    if current_user.role != "super_admin":
        logger.warning(
            f"Non-admin user attempted admin access: id={current_user.id}, "
            f"role={current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Super admin required.",
        )

    logger.debug(f"Super admin access granted: id={current_user.id}")

    return current_user


async def get_current_admin_or_higher(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify admin or super_admin role.

    FastAPI dependency for admin/super_admin routes.

    Args:
        current_user: Current authenticated user

    Returns:
        User model instance (admin or super_admin)

    Raises:
        HTTPException: 403 if user is not admin or super_admin
    """
    if current_user.role not in ["admin", "super_admin"]:
        logger.warning(
            f"Non-admin user attempted admin access: id={current_user.id}, "
            f"role={current_user.role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin required.",
        )

    return current_user


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT refresh token.

    Refresh tokens have longer expiration (typically 7-30 days)
    and are used to obtain new access tokens.

    Args:
        data: Token payload
        expires_delta: Optional custom expiration

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    # Longer expiration for refresh tokens
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.API_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt

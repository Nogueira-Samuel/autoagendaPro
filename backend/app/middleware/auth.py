"""
Authentication Middleware

Request logging and optional authentication middleware.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


async def log_requests_middleware(
    request: Request,
    call_next: Callable,
) -> Response:
    """
    Log all HTTP requests for debugging and monitoring.

    Logs:
    - Request method and path
    - Response status code
    - Request processing time
    - Client IP (if available)

    Usage in main.py:
        from app.middleware.auth import log_requests_middleware
        app.middleware("http")(log_requests_middleware)

    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler

    Returns:
        Response from next handler

    Example:
        INFO - GET /api/v1/appointments?tenant_id=1
        INFO - Status: 200, Duration: 0.123s
    """
    # Start timer
    start_time = time.time()

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - Client: {client_ip}"
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"Status: {response.status_code} - Duration: {duration:.3f}s - "
        f"{request.method} {request.url.path}"
    )

    return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware class for request logging.

    Alternative to function-based middleware for more control.

    Usage in main.py:
        from app.middleware.auth import RequestLoggingMiddleware
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        start_time = time.time()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Log request details
        logger.info(
            f"→ {request.method} {request.url.path} - "
            f"Client: {client_ip} - "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"← Status: {response.status_code} - "
                f"Duration: {duration:.3f}s - "
                f"{request.method} {request.url.path}"
            )

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"✗ Error: {str(e)} - "
                f"Duration: {duration:.3f}s - "
                f"{request.method} {request.url.path}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware (requires Redis).

    Limits requests per IP address using sliding window.

    Usage in main.py:
        from app.middleware.auth import RateLimitMiddleware
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=100,
            window_seconds=60
        )
    """

    def __init__(
        self,
        app,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"

        # Check rate limit using Redis
        from app.utils.redis_client import RedisClient

        # Increment counter
        count = await RedisClient.increment(rate_limit_key)

        # Set expiration on first request
        if count == 1:
            await RedisClient.expire(rate_limit_key, self.window_seconds)

        # Check if limit exceeded
        if count and count > self.max_requests:
            logger.warning(
                f"Rate limit exceeded: {client_ip} - "
                f"{count}/{self.max_requests} requests"
            )

            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests "
                f"per {self.window_seconds} seconds.",
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - (count or 0))
        )

        return response


class CORSDebugMiddleware(BaseHTTPMiddleware):
    """
    Debug middleware for CORS issues.

    Logs CORS-related headers for troubleshooting.

    Usage in main.py (only in development):
        if settings.is_development:
            app.add_middleware(CORSDebugMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log CORS headers."""
        # Log request CORS headers
        logger.debug(f"CORS Request Headers: {request.headers}")
        logger.debug(f"Origin: {request.headers.get('origin', 'not set')}")
        logger.debug(f"Method: {request.method}")

        # Process request
        response = await call_next(request)

        # Log response CORS headers
        logger.debug(f"CORS Response Headers:")
        logger.debug(
            f"  Access-Control-Allow-Origin: "
            f"{response.headers.get('access-control-allow-origin', 'not set')}"
        )
        logger.debug(
            f"  Access-Control-Allow-Methods: "
            f"{response.headers.get('access-control-allow-methods', 'not set')}"
        )

        return response

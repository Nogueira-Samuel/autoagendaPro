"""
Rate Limiting Middleware

Simple rate limiting implementation for API endpoints.
Uses in-memory storage for tracking request counts.
"""

import time
import logging
from collections import defaultdict
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Tracks requests per IP address and enforces rate limits.
    """

    def __init__(self, app):
        super().__init__(app)
        # Store: {ip_address: [(timestamp, count), ...]}
        self.request_counts: defaultdict = defaultdict(list)
        self.window_seconds = 60  # 1 minute window
        self.max_requests = settings.RATE_LIMIT_PER_MINUTE
        self.enabled = settings.RATE_LIMIT_ENABLED

    def _clean_old_requests(self, ip: str, current_time: float) -> None:
        """Remove requests older than the time window."""
        cutoff_time = current_time - self.window_seconds
        self.request_counts[ip] = [
            (ts, count) for ts, count in self.request_counts[ip]
            if ts > cutoff_time
        ]

    def _get_request_count(self, ip: str, current_time: float) -> int:
        """Get total request count for IP in current window."""
        self._clean_old_requests(ip, current_time)
        return sum(count for _, count in self.request_counts[ip])

    def _is_rate_limited(self, ip: str) -> tuple[bool, int]:
        """
        Check if IP address is rate limited.

        Returns:
            (is_limited, remaining_requests)
        """
        current_time = time.time()
        request_count = self._get_request_count(ip, current_time)

        if request_count >= self.max_requests:
            return True, 0

        # Add current request
        self.request_counts[ip].append((current_time, 1))
        remaining = self.max_requests - request_count - 1
        return False, remaining

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and apply rate limiting."""

        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        is_limited, remaining = self._is_rate_limited(client_ip)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}, "
                f"path: {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per minute.",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.window_seconds)),
                    "Retry-After": str(self.window_seconds),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))

        return response

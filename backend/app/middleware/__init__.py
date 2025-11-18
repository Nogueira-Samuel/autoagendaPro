"""
Middleware Package

FastAPI middleware for AutoAgenda Pro:
- tenant: Tenant identification and isolation
- auth: Request logging and authentication
"""

from app.middleware.tenant import get_tenant_from_request
from app.middleware.auth import log_requests_middleware

__all__ = [
    "get_tenant_from_request",
    "log_requests_middleware",
]

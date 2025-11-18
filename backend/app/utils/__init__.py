"""
Utility Functions Package

Helper functions and utilities for AutoAgenda Pro:
- auth: JWT token generation and password hashing
- security: API keys and security helpers
- validators: Custom validation functions
- redis_client: Redis caching client
- timezone_utils: Timezone conversion utilities
"""

from app.utils.auth import (
    create_access_token,
    verify_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    get_current_active_superadmin,
)
from app.utils.security import (
    generate_api_key,
    generate_instance_name,
    sanitize_phone,
)
from app.utils.validators import (
    validate_cpf,
    validate_phone_br,
    validate_time_format,
    validate_date_not_past,
)
from app.utils.redis_client import RedisClient

__all__ = [
    # Auth
    "create_access_token",
    "verify_access_token",
    "get_password_hash",
    "verify_password",
    "get_current_user",
    "get_current_active_superadmin",
    # Security
    "generate_api_key",
    "generate_instance_name",
    "sanitize_phone",
    # Validators
    "validate_cpf",
    "validate_phone_br",
    "validate_time_format",
    "validate_date_not_past",
    # Redis
    "RedisClient",
]

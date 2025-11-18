"""
Security Utilities

Helper functions for security operations like API key generation,
sanitization, and secure random values.
"""

import hashlib
import secrets
import string
from datetime import datetime


def generate_api_key(length: int = 32) -> str:
    """
    Generate secure random API key.

    Uses secrets module for cryptographically strong random generation.
    Suitable for API keys, tokens, and other security-sensitive values.

    Args:
        length: Key length in bytes (default: 32)

    Returns:
        Random hexadecimal string (length * 2 characters)

    Example:
        >>> api_key = generate_api_key()
        >>> print(len(api_key))
        64
        >>> print(api_key)
        a3f5d8e9b2c1f4e8d7a6b5c4f3e2d1a0...
    """
    return secrets.token_hex(length)


def generate_api_key_readable(length: int = 24) -> str:
    """
    Generate readable API key (alphanumeric only).

    Args:
        length: Key length in characters (default: 24)

    Returns:
        Random alphanumeric string

    Example:
        >>> api_key = generate_api_key_readable()
        >>> print(api_key)
        aBcD3fGh1jKlMn0pQrSt
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_instance_name(tenant_name: str) -> str:
    """
    Generate Evolution API instance name from tenant name.

    Creates a URL-safe, unique instance name by:
    1. Removing special characters
    2. Converting to lowercase
    3. Replacing spaces with hyphens
    4. Adding timestamp-based hash for uniqueness

    Args:
        tenant_name: Tenant business name

    Returns:
        URL-safe instance name

    Example:
        >>> name = generate_instance_name("Clínica São Paulo")
        >>> print(name)
        clinica-sao-paulo-a3f5d8
    """
    # Remove special characters and convert to lowercase
    name = tenant_name.lower()
    name = "".join(c if c.isalnum() or c == " " else "" for c in name)

    # Replace spaces with hyphens
    name = name.replace(" ", "-")

    # Remove multiple consecutive hyphens
    while "--" in name:
        name = name.replace("--", "-")

    # Strip leading/trailing hyphens
    name = name.strip("-")

    # Limit length
    name = name[:50]

    # Add timestamp hash for uniqueness
    timestamp = str(int(datetime.utcnow().timestamp()))
    hash_suffix = hashlib.md5(timestamp.encode()).hexdigest()[:6]

    return f"{name}-{hash_suffix}"


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number (remove non-numeric characters).

    Args:
        phone: Phone number with any formatting

    Returns:
        Numeric-only phone string

    Example:
        >>> sanitize_phone("+55 (21) 99999-9999")
        '5521999999999'
        >>> sanitize_phone("(21) 9.9999.9999")
        '21999999999'
    """
    return "".join(filter(str.isdigit, phone))


def sanitize_email(email: str) -> str:
    """
    Sanitize email (lowercase, strip whitespace).

    Args:
        email: Email address

    Returns:
        Sanitized email

    Example:
        >>> sanitize_email("  User@Example.COM  ")
        'user@example.com'
    """
    return email.strip().lower()


def generate_verification_code(length: int = 6) -> str:
    """
    Generate numeric verification code.

    Useful for SMS/email verification, 2FA, etc.

    Args:
        length: Code length (default: 6)

    Returns:
        Numeric string

    Example:
        >>> code = generate_verification_code()
        >>> print(code)
        '123456'
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash string using specified algorithm.

    Args:
        value: String to hash
        algorithm: Hash algorithm (md5, sha256, sha512)

    Returns:
        Hexadecimal hash string

    Example:
        >>> hash_string("test@example.com")
        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'
    """
    if algorithm == "md5":
        return hashlib.md5(value.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(value.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(value.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate URL-friendly slug from text.

    Args:
        text: Text to slugify
        max_length: Maximum slug length

    Returns:
        URL-safe slug

    Example:
        >>> generate_slug("My Business Name!")
        'my-business-name'
    """
    # Convert to lowercase
    slug = text.lower()

    # Remove special characters
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)

    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")

    # Remove multiple consecutive hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    # Limit length
    return slug[:max_length]


def mask_email(email: str) -> str:
    """
    Mask email for privacy (show first char and domain).

    Args:
        email: Email address

    Returns:
        Masked email

    Example:
        >>> mask_email("john.doe@example.com")
        'j*******@example.com'
    """
    if "@" not in email:
        return email

    local, domain = email.split("@", 1)

    if len(local) <= 1:
        masked_local = local
    else:
        masked_local = local[0] + "*" * (len(local) - 1)

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for privacy.

    Args:
        phone: Phone number

    Returns:
        Masked phone number

    Example:
        >>> mask_phone("5521999999999")
        '55219****9999'
    """
    phone = sanitize_phone(phone)

    if len(phone) <= 4:
        return phone

    # Show first 5 and last 4 digits
    return phone[:5] + "*" * (len(phone) - 9) + phone[-4:]


def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
) -> str:
    """
    Generate secure random password.

    Args:
        length: Password length
        include_uppercase: Include uppercase letters
        include_lowercase: Include lowercase letters
        include_digits: Include digits
        include_symbols: Include symbols

    Returns:
        Random password

    Example:
        >>> password = generate_password(length=12)
        >>> print(len(password))
        12
    """
    alphabet = ""

    if include_uppercase:
        alphabet += string.ascii_uppercase
    if include_lowercase:
        alphabet += string.ascii_lowercase
    if include_digits:
        alphabet += string.digits
    if include_symbols:
        alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if not alphabet:
        raise ValueError("At least one character type must be included")

    # Ensure at least one character from each selected type
    password = []

    if include_uppercase:
        password.append(secrets.choice(string.ascii_uppercase))
    if include_lowercase:
        password.append(secrets.choice(string.ascii_lowercase))
    if include_digits:
        password.append(secrets.choice(string.digits))
    if include_symbols:
        password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

    # Fill remaining length with random characters
    for _ in range(length - len(password)):
        password.append(secrets.choice(alphabet))

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return "".join(password)

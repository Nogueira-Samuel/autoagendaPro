"""
Custom Validators

Validation functions for Brazilian-specific formats (CPF, phone)
and general validations (time, date, etc).
"""

import re
from datetime import date, datetime, time


def validate_cpf(cpf: str) -> bool:
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).

    CPF is an 11-digit taxpayer identification number.
    Uses check digit algorithm to validate.

    Args:
        cpf: CPF string (with or without formatting)

    Returns:
        True if valid CPF, False otherwise

    Example:
        >>> validate_cpf("123.456.789-09")
        True
        >>> validate_cpf("11111111111")
        False
        >>> validate_cpf("123.456.789-00")
        False
    """
    # Remove non-numeric characters
    cpf = "".join(filter(str.isdigit, cpf))

    # Must have exactly 11 digits
    if len(cpf) != 11:
        return False

    # Check if all digits are the same (invalid CPF)
    if cpf == cpf[0] * 11:
        return False

    # Calculate first check digit
    def calc_digit(cpf_slice: str) -> int:
        """Calculate check digit."""
        sum_val = sum(
            (len(cpf_slice) + 1 - i) * int(d) for i, d in enumerate(cpf_slice)
        )
        remainder = sum_val % 11
        return 0 if remainder < 2 else 11 - remainder

    # Validate first check digit (position 9)
    if int(cpf[9]) != calc_digit(cpf[:9]):
        return False

    # Validate second check digit (position 10)
    if int(cpf[10]) != calc_digit(cpf[:10]):
        return False

    return True


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate Brazilian CNPJ (Cadastro Nacional da Pessoa Jurídica).

    CNPJ is a 14-digit company identification number.

    Args:
        cnpj: CNPJ string (with or without formatting)

    Returns:
        True if valid CNPJ, False otherwise

    Example:
        >>> validate_cnpj("11.222.333/0001-81")
        True
        >>> validate_cnpj("00.000.000/0000-00")
        False
    """
    # Remove non-numeric characters
    cnpj = "".join(filter(str.isdigit, cnpj))

    # Must have exactly 14 digits
    if len(cnpj) != 14:
        return False

    # Check if all digits are the same (invalid CNPJ)
    if cnpj == cnpj[0] * 14:
        return False

    # Calculate check digits
    def calc_digit(cnpj_slice: str, weights: list[int]) -> int:
        """Calculate check digit with given weights."""
        sum_val = sum(int(d) * w for d, w in zip(cnpj_slice, weights))
        remainder = sum_val % 11
        return 0 if remainder < 2 else 11 - remainder

    # First check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    if int(cnpj[12]) != calc_digit(cnpj[:12], weights1):
        return False

    # Second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    if int(cnpj[13]) != calc_digit(cnpj[:13], weights2):
        return False

    return True


def validate_phone_br(phone: str) -> bool:
    """
    Validate Brazilian phone number format.

    Expected format: 55 (country) + DDD (2 digits) + number (8-9 digits)
    Total: 12-13 digits

    Args:
        phone: Phone string

    Returns:
        True if valid Brazilian phone, False otherwise

    Example:
        >>> validate_phone_br("5521999999999")  # Mobile
        True
        >>> validate_phone_br("552133334444")   # Landline
        True
        >>> validate_phone_br("21999999999")    # Missing country code
        False
        >>> validate_phone_br("55009999999")    # Invalid DDD
        False
    """
    # Remove non-numeric characters
    phone = "".join(filter(str.isdigit, phone))

    # Must start with country code 55
    if not phone.startswith("55"):
        return False

    # Remove country code for validation
    phone_without_code = phone[2:]

    # Must have 10 or 11 digits (DDD + number)
    if len(phone_without_code) not in [10, 11]:
        return False

    # Extract DDD (area code)
    ddd = int(phone_without_code[:2])

    # Valid DDD range: 11-99 (Brazilian area codes)
    if ddd < 11 or ddd > 99:
        return False

    # If 11 digits, first digit after DDD must be 9 (mobile)
    if len(phone_without_code) == 11:
        if phone_without_code[2] != "9":
            return False

    return True


def validate_time_format(time_str: str) -> bool:
    """
    Validate time string format (HH:MM).

    Args:
        time_str: Time string

    Returns:
        True if valid time format

    Example:
        >>> validate_time_format("09:30")
        True
        >>> validate_time_format("23:59")
        True
        >>> validate_time_format("24:00")
        False
        >>> validate_time_format("9:30")
        False
    """
    # Pattern: HH:MM (00:00 to 23:59)
    pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
    return bool(re.match(pattern, time_str))


def parse_time_string(time_str: str) -> time | None:
    """
    Parse time string to time object.

    Args:
        time_str: Time string in HH:MM format

    Returns:
        time object or None if invalid

    Example:
        >>> t = parse_time_string("14:30")
        >>> print(t)
        14:30:00
    """
    if not validate_time_format(time_str):
        return None

    try:
        hour, minute = map(int, time_str.split(":"))
        return time(hour=hour, minute=minute)
    except ValueError:
        return None


def validate_date_not_past(date_obj: date) -> bool:
    """
    Validate that date is not in the past.

    Args:
        date_obj: Date to validate

    Returns:
        True if today or future date

    Example:
        >>> from datetime import date, timedelta
        >>> validate_date_not_past(date.today())
        True
        >>> validate_date_not_past(date.today() + timedelta(days=1))
        True
        >>> validate_date_not_past(date.today() - timedelta(days=1))
        False
    """
    return date_obj >= date.today()


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that end_date is after start_date.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        True if valid range

    Example:
        >>> from datetime import date
        >>> start = date(2024, 1, 1)
        >>> end = date(2024, 12, 31)
        >>> validate_date_range(start, end)
        True
    """
    return end_date >= start_date


def validate_business_hours(open_time: str, close_time: str) -> bool:
    """
    Validate business hours (open must be before close).

    Args:
        open_time: Opening time (HH:MM)
        close_time: Closing time (HH:MM)

    Returns:
        True if valid business hours

    Example:
        >>> validate_business_hours("09:00", "18:00")
        True
        >>> validate_business_hours("18:00", "09:00")
        False
    """
    if not validate_time_format(open_time) or not validate_time_format(close_time):
        return False

    open_t = parse_time_string(open_time)
    close_t = parse_time_string(close_time)

    if not open_t or not close_t:
        return False

    return open_t < close_t


def validate_hex_color(color: str) -> bool:
    """
    Validate hexadecimal color code.

    Args:
        color: Hex color string

    Returns:
        True if valid hex color

    Example:
        >>> validate_hex_color("#FF5733")
        True
        >>> validate_hex_color("#fff")
        True
        >>> validate_hex_color("FF5733")
        True
        >>> validate_hex_color("#GG5733")
        False
    """
    # Remove # if present
    color = color.lstrip("#")

    # Must be 3 or 6 hex digits
    if len(color) not in [3, 6]:
        return False

    # All characters must be hex digits
    try:
        int(color, 16)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format (basic validation).

    Args:
        url: URL string

    Returns:
        True if valid URL format

    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("http://example.com/path?query=1")
        True
        >>> validate_url("not a url")
        False
    """
    # Basic URL pattern
    pattern = r"^https?://[\w\-.]+(:\d+)?(/[\w\-./]*)?(\?[\w\-=&]*)?(#[\w\-]*)?$"
    return bool(re.match(pattern, url))


def validate_password_strength(password: str) -> dict[str, bool]:
    """
    Check password strength against multiple criteria.

    Args:
        password: Password string

    Returns:
        Dictionary with strength criteria and results

    Example:
        >>> result = validate_password_strength("MyP@ssw0rd")
        >>> print(result)
        {
            'min_length': True,
            'has_uppercase': True,
            'has_lowercase': True,
            'has_digit': True,
            'has_special': True,
            'is_strong': True
        }
    """
    return {
        "min_length": len(password) >= 8,
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password)),
        "is_strong": (
            len(password) >= 8
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"\d", password)
        ),
    }


def sanitize_string(text: str, max_length: int | None = None) -> str:
    """
    Sanitize string by removing dangerous characters.

    Args:
        text: Text to sanitize
        max_length: Optional maximum length

    Returns:
        Sanitized string

    Example:
        >>> sanitize_string("<script>alert('xss')</script>")
        "scriptalert('xss')/script"
    """
    # Remove common XSS characters
    dangerous_chars = ["<", ">", "&", '"', "'", "/", "\\"]

    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Limit length if specified
    if max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()

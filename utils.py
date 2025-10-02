
"""Utility functions for data validation.

Contains email validation and numeric validation helpers used throughout
the School Management System.
"""

import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def is_valid_email(email: str) -> bool:
    """Validate an email address using regex.
    
    :param email: Email string to validate.
    :type email: str
    :return: True if email format is valid, False otherwise.
    :rtype: bool
    """
    return bool(EMAIL_RE.match(email or ""))

def non_negative_int(value) -> bool:
    """Check if a value can be converted to a non-negative integer.
    
    :param value: Value to check (any type).
    :return: True if value is a non-negative integer, False otherwise.
    :rtype: bool
    """
    try:
        return int(value) >= 0
    except Exception:
        return False

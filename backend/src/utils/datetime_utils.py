"""
Datetime utilities for consistent timestamp handling across the application.
"""

from datetime import datetime, timezone


def now() -> datetime:
    """
    Get the current datetime in the local timezone.

    This replaces datetime.utcnow() to provide local timestamps
    instead of UTC timestamps throughout the application.

    Returns:
        datetime: Current local datetime
    """
    return datetime.now()


def utc_now() -> datetime:
    """
    Get the current datetime in UTC timezone.

    Use this when you specifically need UTC time.

    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)
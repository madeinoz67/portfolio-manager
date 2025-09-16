"""
Datetime utilities for consistent timestamp handling across the application.

IMPORTANT NOTE FOR FUTURE DEVELOPERS:
=====================================
When working with datetime fields that will be sent to the frontend, ALWAYS use
to_iso_string() instead of .isoformat() directly. Here's why:

WRONG (causes JavaScript "Invalid Date"):
    "created_at": some_datetime.isoformat() + "Z"  # Creates "+00:00Z" format
    "updated_at": some_datetime.isoformat()        # Missing timezone info

CORRECT (works with JavaScript Date constructor):
    "created_at": to_iso_string(some_datetime)
    "updated_at": to_iso_string(some_datetime)

The to_iso_string() function handles:
- Timezone-aware datetimes: Uses existing timezone info
- Naive datetimes: Assumes UTC and adds proper "Z" suffix
- Prevents the invalid "+00:00Z" pattern that breaks JavaScript parsing

Always follow this pattern in API responses, logging, and any data sent to frontend.
"""

from datetime import datetime, timezone


def now() -> datetime:
    """
    Get the current datetime in UTC timezone.

    Following FastAPI timezone best practices, this function returns
    timezone-aware UTC datetime for consistent handling across the application.
    This ensures all timestamps are in UTC for database storage and API responses.

    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def utc_now() -> datetime:
    """
    Get the current datetime in UTC timezone.

    Use this when you specifically need UTC time.

    Returns:
        datetime: Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """
    Convert a datetime to a properly formatted ISO string for frontend consumption.

    Handles both timezone-aware and naive datetimes correctly.
    For timezone-aware datetimes, uses the existing timezone info.
    For naive datetimes, treats them as UTC and adds Z suffix.

    Args:
        dt: The datetime to format

    Returns:
        str: ISO formatted datetime string that JavaScript Date can parse
    """
    if dt is None:
        return None

    if dt.tzinfo is not None:
        # Timezone-aware datetime - convert to UTC and use Z suffix
        if dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)  # Convert to UTC if not already
        # Use Z suffix for UTC timezone (JavaScript-friendly format)
        return dt.replace(tzinfo=None).isoformat() + "Z"
    else:
        # Naive datetime - assume UTC and add Z suffix
        return dt.isoformat() + "Z"
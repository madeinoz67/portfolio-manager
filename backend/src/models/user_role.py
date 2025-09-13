"""
User role enumeration for role-based access control.
"""

import enum


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"
    USER = "user"
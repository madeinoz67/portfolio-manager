"""
User model for authentication and profile management.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from src.utils.datetime_utils import now

from sqlalchemy import Boolean, Column, DateTime, String, Text, Uuid, Enum
from sqlalchemy.orm import relationship

from src.database import Base
from .user_role import UserRole

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .portfolio import Portfolio


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    email_config = Column(Text)  # JSON string for OAuth tokens, broker settings

    # Relationships
    portfolios = relationship(
        "Portfolio", back_populates="owner", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
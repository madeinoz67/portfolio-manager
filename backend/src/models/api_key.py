"""
API Key model for user authentication.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from src.utils.datetime_utils import now

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .user import User


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(Text)  # JSON string for permissions
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)

    # Relationships
    user: "User" = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"
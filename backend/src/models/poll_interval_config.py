"""
Database model for poll interval configurations.

Tracks administrative settings for market data polling frequencies.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base


class PollIntervalConfig(Base):
    """Model for poll interval configuration records."""

    __tablename__ = "poll_interval_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interval_minutes = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    created_by = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expired_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<PollIntervalConfig(id={self.id}, interval={self.interval_minutes}min, active={self.is_active})>"
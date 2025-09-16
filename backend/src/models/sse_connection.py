"""
Database model for tracking active SSE connections.

Manages Server-Sent Events connections for real-time market data updates.
"""

from datetime import datetime
from typing import Optional
import uuid

from src.utils.datetime_utils import now

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class SSEConnection(Base):
    """Model for tracking active Server-Sent Events connections."""

    __tablename__ = "sse_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(String(100), unique=True, nullable=False, index=True)  # Unique connection identifier
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    client_ip = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(String(500), nullable=True)
    subscribed_symbols = Column(JSON, nullable=True)  # List of symbols client is interested in
    portfolio_ids = Column(JSON, nullable=True)  # List of portfolio IDs for updates
    connection_type = Column(String(20), default="market_data", nullable=False)  # 'market_data', 'portfolio', etc.
    is_active = Column(Boolean, default=True, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    messages_sent = Column(Integer, default=0, nullable=False)
    connected_at = Column(DateTime, default=now, nullable=False)
    disconnected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)

    # Relationships
    user = relationship("User", lazy="select")

    @property
    def is_stale(self) -> bool:
        """Check if connection hasn't sent heartbeat in over 5 minutes."""
        if self.last_heartbeat is None:
            return False
        return (now() - self.last_heartbeat).total_seconds() > 300

    def __repr__(self) -> str:
        return f"<SSEConnection(id={self.connection_id}, user_id={self.user_id}, active={self.is_active})>"
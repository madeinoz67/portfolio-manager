"""
AuditLog model for tracking all portfolio and transaction events.
Provides comprehensive audit trail for administrative oversight.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, JSON, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship
from src.database import Base
from src.utils.datetime_utils import now


class AuditEventType(enum.Enum):
    """Enumeration of all possible audit event types."""

    # Portfolio events
    PORTFOLIO_CREATED = "portfolio_created"
    PORTFOLIO_UPDATED = "portfolio_updated"
    PORTFOLIO_DELETED = "portfolio_deleted"
    PORTFOLIO_SOFT_DELETED = "portfolio_soft_deleted"
    PORTFOLIO_HARD_DELETED = "portfolio_hard_deleted"

    # Transaction events
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_UPDATED = "transaction_updated"
    TRANSACTION_DELETED = "transaction_deleted"

    # Holding events
    HOLDING_CREATED = "holding_created"
    HOLDING_UPDATED = "holding_updated"
    HOLDING_DELETED = "holding_deleted"

    # User/Auth events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"

    # Admin events
    ADMIN_ACTION_PERFORMED = "admin_action_performed"

    # Market data provider admin events
    PROVIDER_ENABLED = "provider_enabled"
    PROVIDER_DISABLED = "provider_disabled"
    PROVIDER_PAUSED = "provider_paused"
    PROVIDER_RESUMED = "provider_resumed"
    PROVIDER_CONFIGURED = "provider_configured"

    # Scheduler admin events
    SCHEDULER_STARTED = "scheduler_started"
    SCHEDULER_STOPPED = "scheduler_stopped"
    SCHEDULER_PAUSED = "scheduler_paused"
    SCHEDULER_RESUMED = "scheduler_resumed"
    SCHEDULER_CONFIGURED = "scheduler_configured"

    # System admin events
    SYSTEM_MAINTENANCE_START = "system_maintenance_start"
    SYSTEM_MAINTENANCE_END = "system_maintenance_end"


class AuditLog(Base):
    """
    AuditLog model for comprehensive event tracking.

    Captures all portfolio and transaction events with full context
    for administrative oversight and user accountability.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    event_description = Column(Text, nullable=False)

    # User context
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)

    # Entity context
    entity_type = Column(String(50), nullable=False, index=True)  # portfolio, transaction, holding, etc.
    entity_id = Column(String(100), nullable=False, index=True)   # ID of the affected entity

    # Timing
    timestamp = Column(DateTime, nullable=False, default=now, index=True)

    # Additional context
    event_metadata = Column(JSON, nullable=True)  # Additional event-specific data
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)        # Browser/client info

    # Record management
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.event_type.value} by user {self.user_id} on {self.entity_type} {self.entity_id}>"


# Create indexes for efficient querying
Index('idx_audit_logs_user_event_time', AuditLog.user_id, AuditLog.event_type, AuditLog.timestamp)
Index('idx_audit_logs_entity', AuditLog.entity_type, AuditLog.entity_id)
Index('idx_audit_logs_timestamp_desc', AuditLog.timestamp.desc())
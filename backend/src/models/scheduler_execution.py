"""
Database model for scheduler execution tracking.

Stores execution history to persist scheduler state across application restarts.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

from src.database import Base


class SchedulerExecution(Base):
    """
    Model for tracking scheduler execution history.

    Stores detailed information about each scheduler run to maintain
    state persistence across FastAPI restarts and reloads.
    """
    __tablename__ = "scheduler_executions"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # 'success', 'failed', 'cancelled'

    # Execution metrics
    symbols_processed = Column(Integer, default=0)
    successful_fetches = Column(Integer, default=0)
    failed_fetches = Column(Integer, default=0)
    execution_time_ms = Column(Integer, nullable=True)

    # Provider information
    provider_used = Column(String(50), nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)

    # Additional metadata as JSON
    execution_metadata = Column(Text, nullable=True)  # JSON string for flexible data storage

    def __repr__(self):
        return (
            f"<SchedulerExecution(id={self.id}, status='{self.status}', "
            f"started_at='{self.started_at}', symbols={self.symbols_processed})>"
        )

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary."""
        if self.execution_metadata:
            try:
                return json.loads(self.execution_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metadata(self, data: Dict[str, Any]) -> None:
        """Set metadata from dictionary."""
        self.execution_metadata = json.dumps(data) if data else None

    @property
    def execution_duration_seconds(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this execution."""
        total = self.successful_fetches + self.failed_fetches
        if total > 0:
            return (self.successful_fetches / total) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "symbols_processed": self.symbols_processed,
            "successful_fetches": self.successful_fetches,
            "failed_fetches": self.failed_fetches,
            "execution_time_ms": self.execution_time_ms,
            "provider_used": self.provider_used,
            "error_message": self.error_message,
            "metadata": self.get_metadata(),
            "execution_duration_seconds": self.execution_duration_seconds,
            "success_rate": self.success_rate
        }
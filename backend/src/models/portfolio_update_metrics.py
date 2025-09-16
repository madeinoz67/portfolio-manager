"""
Database models for portfolio update metrics and monitoring.

Tracks performance, health, and efficiency of the real-time portfolio update system.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.utils.datetime_utils import now


class PortfolioUpdateMetric(Base):
    """
    Tracks individual portfolio update operations.

    Records performance, success/failure, and metadata for each portfolio update
    triggered by market data changes or manual requests.
    """

    __tablename__ = "portfolio_update_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(String(36), nullable=False, index=True)  # Portfolio UUID as string

    # Update details
    symbols_updated = Column(JSON, nullable=False)  # List of symbols that triggered update
    symbols_count = Column(Integer, nullable=False, default=1)
    update_duration_ms = Column(Integer, nullable=False)  # Time taken for update

    # Status and result
    status = Column(String(20), nullable=False, index=True)  # success, error, timeout, rate_limited
    trigger_type = Column(String(50), nullable=False, index=True)  # market_data_change, bulk_market_data, manual_refresh
    update_source = Column(String(30), nullable=False)  # automated, user_requested, admin_triggered

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String(50), nullable=True, index=True)

    # Performance metrics
    queue_wait_time_ms = Column(Integer, nullable=True)  # Time spent in queue before processing
    db_query_time_ms = Column(Integer, nullable=True)   # Time spent on database operations
    calculation_time_ms = Column(Integer, nullable=True) # Time spent calculating portfolio values

    # Storm protection metrics
    coalesced_count = Column(Integer, nullable=True)  # Number of individual updates that were merged
    debounce_delay_ms = Column(Integer, nullable=True)  # Time delayed due to debouncing

    # Timing analysis
    price_change_timestamp = Column(DateTime, nullable=True)  # When price change occurred
    queue_entry_timestamp = Column(DateTime, nullable=True)   # When update was queued
    processing_start_timestamp = Column(DateTime, nullable=True)  # When processing started

    # System metadata
    created_at = Column(DateTime, default=now, nullable=False, index=True)
    extra_data = Column(JSON, nullable=True)  # Additional context and debugging info

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_portfolio_update_metrics_portfolio_status', 'portfolio_id', 'status'),
        Index('idx_portfolio_update_metrics_created_status', 'created_at', 'status'),
        Index('idx_portfolio_update_metrics_trigger_type', 'trigger_type', 'created_at'),
        Index('idx_portfolio_update_metrics_performance', 'update_duration_ms', 'status'),
    )

    def __repr__(self) -> str:
        return f"<PortfolioUpdateMetric(id={self.id}, portfolio_id={self.portfolio_id}, status={self.status}, duration={self.update_duration_ms}ms)>"


class PortfolioQueueMetric(Base):
    """
    Tracks portfolio update queue health and performance over time.

    Records queue size, processing rates, and resource usage for monitoring
    the real-time update system's health and identifying bottlenecks.
    """

    __tablename__ = "portfolio_queue_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Queue status
    pending_updates = Column(Integer, nullable=False, default=0)
    processing_rate = Column(Numeric(8, 2), nullable=False, default=0.0)  # Updates per minute
    active_portfolios = Column(Integer, nullable=False, default=0)  # Portfolios with pending updates

    # Performance indicators
    avg_processing_time_ms = Column(Integer, nullable=True)
    max_processing_time_ms = Column(Integer, nullable=True)
    queue_throughput = Column(Numeric(8, 2), nullable=True)  # Processed updates per minute

    # Storm protection effectiveness
    rate_limit_hits = Column(Integer, nullable=False, default=0)
    coalesced_updates = Column(Integer, nullable=False, default=0)
    debounce_savings = Column(Integer, nullable=False, default=0)  # Updates prevented by debouncing

    # Resource usage
    memory_usage_mb = Column(Numeric(8, 2), nullable=True)
    cpu_usage_percent = Column(Numeric(5, 2), nullable=True)
    database_connections = Column(Integer, nullable=True)

    # System health indicators
    is_processing = Column(Boolean, nullable=False, default=True)
    last_successful_update = Column(DateTime, nullable=True)
    error_count_last_hour = Column(Integer, nullable=False, default=0)

    # Configuration snapshot
    debounce_seconds = Column(Numeric(4, 1), nullable=True)
    max_updates_per_minute = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=now, nullable=False, index=True)
    extra_data = Column(JSON, nullable=True)  # Additional queue state information

    # Indexes for time-series analysis
    __table_args__ = (
        Index('idx_portfolio_queue_metrics_created', 'created_at'),
        Index('idx_portfolio_queue_metrics_processing', 'is_processing', 'created_at'),
        Index('idx_portfolio_queue_metrics_performance', 'processing_rate', 'pending_updates'),
    )

    def __repr__(self) -> str:
        return f"<PortfolioQueueMetric(id={self.id}, pending={self.pending_updates}, rate={self.processing_rate}, active={self.active_portfolios})>"


class PortfolioUpdateSummary(Base):
    """
    Aggregated portfolio update statistics for efficient dashboard queries.

    Pre-calculated summaries by hour/day to avoid expensive real-time aggregations
    on large metrics tables. Updated periodically by background jobs.
    """

    __tablename__ = "portfolio_update_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(10), nullable=False, index=True)  # hour, day, week

    # Update statistics
    total_updates = Column(Integer, nullable=False, default=0)
    successful_updates = Column(Integer, nullable=False, default=0)
    failed_updates = Column(Integer, nullable=False, default=0)
    rate_limited_updates = Column(Integer, nullable=False, default=0)

    # Performance metrics
    avg_update_duration_ms = Column(Integer, nullable=True)
    median_update_duration_ms = Column(Integer, nullable=True)
    p95_update_duration_ms = Column(Integer, nullable=True)
    max_update_duration_ms = Column(Integer, nullable=True)

    # Efficiency metrics
    total_symbols_processed = Column(Integer, nullable=False, default=0)
    coalesced_updates_count = Column(Integer, nullable=False, default=0)
    coalescing_efficiency = Column(Numeric(5, 2), nullable=True)  # Percentage

    # Coverage metrics
    unique_portfolios = Column(Integer, nullable=False, default=0)
    unique_symbols = Column(Integer, nullable=False, default=0)
    avg_portfolios_per_symbol = Column(Numeric(8, 2), nullable=True)

    # Lag analysis
    avg_update_lag_ms = Column(Integer, nullable=True)
    median_update_lag_ms = Column(Integer, nullable=True)
    p95_update_lag_ms = Column(Integer, nullable=True)
    max_update_lag_ms = Column(Integer, nullable=True)

    # Queue health during period
    avg_queue_size = Column(Numeric(8, 2), nullable=True)
    max_queue_size = Column(Integer, nullable=True)
    avg_processing_rate = Column(Numeric(8, 2), nullable=True)

    # Resource usage
    avg_memory_usage_mb = Column(Numeric(8, 2), nullable=True)
    max_memory_usage_mb = Column(Numeric(8, 2), nullable=True)
    avg_cpu_usage_percent = Column(Numeric(5, 2), nullable=True)

    # Error analysis
    top_error_types = Column(JSON, nullable=True)  # Dict of error_type: count
    error_rate = Column(Numeric(5, 2), nullable=True)  # Percentage

    # System health
    uptime_percentage = Column(Numeric(5, 2), nullable=True)
    service_interruptions = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # Indexes for dashboard queries
    __table_args__ = (
        Index('idx_portfolio_update_summaries_period', 'period_type', 'period_start'),
        Index('idx_portfolio_update_summaries_performance', 'period_start', 'avg_update_duration_ms'),
        Index('idx_portfolio_update_summaries_created', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<PortfolioUpdateSummary(period_start={self.period_start}, period_type={self.period_type}, total_updates={self.total_updates})>"


class PortfolioUpdateAlert(Base):
    """
    Tracks alerts and anomalies in portfolio update system performance.

    Stores triggered alerts for degraded performance, high error rates,
    queue backlog issues, etc. for operational monitoring.
    """

    __tablename__ = "portfolio_update_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # high_error_rate, queue_backlog, slow_updates
    severity = Column(String(20), nullable=False, index=True)   # info, warning, error, critical
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Alert conditions
    threshold_value = Column(Numeric(12, 4), nullable=True)
    actual_value = Column(Numeric(12, 4), nullable=True)
    metric_name = Column(String(100), nullable=True)

    # Context
    affected_portfolios = Column(JSON, nullable=True)  # List of portfolio IDs
    time_period = Column(String(50), nullable=True)    # "last_15_minutes", "last_hour"

    # Resolution
    is_resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(Text, nullable=True)
    auto_resolved = Column(Boolean, nullable=False, default=False)

    # Notification
    notification_sent = Column(Boolean, nullable=False, default=False)
    notification_channels = Column(JSON, nullable=True)  # List of channels notified

    # Timestamps
    first_occurred_at = Column(DateTime, nullable=False, index=True)
    last_occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    # Additional context
    extra_data = Column(JSON, nullable=True)

    # Indexes for alert management
    __table_args__ = (
        Index('idx_portfolio_update_alerts_type_severity', 'alert_type', 'severity'),
        Index('idx_portfolio_update_alerts_active', 'is_resolved', 'first_occurred_at'),
        Index('idx_portfolio_update_alerts_recent', 'created_at', 'severity'),
    )

    def __repr__(self) -> str:
        return f"<PortfolioUpdateAlert(id={self.id}, type={self.alert_type}, severity={self.severity}, resolved={self.is_resolved})>"
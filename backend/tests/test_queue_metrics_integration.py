"""
Integration test to verify queue metrics recording actually works with the fix.
"""

import pytest
import time
from sqlalchemy.orm import Session

from src.services.portfolio_update_queue import PortfolioUpdateQueue
from src.models.portfolio_update_metrics import PortfolioQueueMetric
from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService


def test_queue_metrics_recording_integration(db_session: Session):
    """
    Integration test to verify that queue metrics are automatically recorded.
    This tests the actual fix we implemented.
    """
    # Clear any existing metrics
    db_session.query(PortfolioQueueMetric).delete()
    db_session.commit()

    # Create queue and manually trigger metrics recording
    queue = PortfolioUpdateQueue(debounce_seconds=0.1, max_updates_per_minute=100)

    # Manually trigger metrics recording (simulates what happens in background task)
    queue._record_queue_metrics(db_session)
    db_session.commit()  # Commit the transaction

    # Verify that a PortfolioQueueMetric record was created
    metrics = db_session.query(PortfolioQueueMetric).all()
    assert len(metrics) == 1, f"Expected 1 queue metric record, got {len(metrics)}"

    # Verify the metric has valid data
    metric = metrics[0]
    assert metric.pending_updates == 0, "Should have 0 pending updates initially"
    assert metric.processing_rate == 0, "Should have 0 processing rate initially"
    assert metric.memory_usage_mb >= 50.0, "Should have base memory usage"
    assert metric.is_processing is not None, "Should have processing status"
    assert metric.created_at is not None, "Should have creation timestamp"

    # Test queue health calculation with this metric
    metrics_service = PortfolioUpdateMetricsService(db_session)
    health = metrics_service.get_queue_health_metrics()

    # CRITICAL VERIFICATION: Health should no longer be "unknown"
    assert health["queue_health_status"] != "unknown", \
        f"Queue health status should not be unknown, got {health['queue_health_status']}"
    assert health["queue_health_status"] in ["healthy", "warning", "critical"], \
        f"Should have valid health status, got {health['queue_health_status']}"


def test_queue_metrics_with_simulated_activity(db_session: Session):
    """
    Test queue metrics recording with simulated queue activity.
    """
    # Clear any existing metrics
    db_session.query(PortfolioQueueMetric).delete()
    db_session.commit()

    queue = PortfolioUpdateQueue(debounce_seconds=0.1, max_updates_per_minute=100)

    # Simulate some queue activity
    queue.queue_portfolio_update("portfolio_1", ["AAPL", "GOOGL"], priority=1)
    queue.queue_portfolio_update("portfolio_2", ["MSFT", "TSLA"], priority=1)

    # Wait a moment to simulate some activity time
    time.sleep(0.1)

    # Record metrics
    queue._record_queue_metrics(db_session)
    db_session.commit()

    # Verify metrics capture the queue activity
    metrics = db_session.query(PortfolioQueueMetric).all()
    assert len(metrics) == 1, "Should have one metric record"

    metric = metrics[0]
    assert metric.pending_updates == 2, f"Should have 2 pending updates, got {metric.pending_updates}"
    assert metric.active_portfolios == 2, f"Should have 2 active portfolios, got {metric.active_portfolios}"

    # Test that health calculation works with realistic data
    metrics_service = PortfolioUpdateMetricsService(db_session)
    health = metrics_service.get_queue_health_metrics()

    assert health["current_queue_size"] == 2, "Should show current queue size"
    assert health["queue_health_status"] == "healthy", "Should be healthy with small queue"


def test_queue_metrics_interval_respects_timing(db_session: Session):
    """
    Test that metrics are only recorded at the specified interval.
    """
    # Clear any existing metrics
    db_session.query(PortfolioQueueMetric).delete()
    db_session.commit()

    queue = PortfolioUpdateQueue(debounce_seconds=0.1, max_updates_per_minute=100)

    # Set a long metrics interval
    queue._metrics_interval = 60.0  # 1 minute

    # First call should record metrics
    queue._record_queue_metrics(db_session)
    db_session.commit()

    metrics_count_1 = db_session.query(PortfolioQueueMetric).count()
    assert metrics_count_1 == 1, "First call should record metrics"

    # Second call immediately should NOT record more metrics
    queue._record_queue_metrics(db_session)
    db_session.commit()

    metrics_count_2 = db_session.query(PortfolioQueueMetric).count()
    assert metrics_count_2 == 1, "Second immediate call should not record more metrics"

    # Reset the timer to simulate time passing
    queue._last_metrics_time = 0

    # Third call should record metrics again
    queue._record_queue_metrics(db_session)
    db_session.commit()

    metrics_count_3 = db_session.query(PortfolioQueueMetric).count()
    assert metrics_count_3 == 2, "Third call after timer reset should record more metrics"
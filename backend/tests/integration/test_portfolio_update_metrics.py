"""
Integration tests for portfolio update monitoring metrics.
Tests metrics collection, storage, and retrieval for admin dashboard.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from src.models import Portfolio, User, Stock, Holding, MarketDataProvider
from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService
from src.services.portfolio_update_queue import PortfolioUpdateQueue


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="metrics@example.com",
        password_hash="$2b$12$dummy.hash.value",
        first_name="Metrics",
        last_name="Test"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_portfolios(db: Session, test_user: User):
    """Create test portfolios."""
    portfolios = []
    for i in range(5):
        portfolio = Portfolio(
            name=f"Metrics Portfolio {i}",
            description=f"Portfolio for metrics testing {i}",
            owner_id=test_user.id,
            total_value=Decimal("10000.00"),
            daily_change=Decimal("100.00"),
            daily_change_percent=Decimal("1.00")
        )
        db.add(portfolio)
        portfolios.append(portfolio)

    db.commit()
    for portfolio in portfolios:
        db.refresh(portfolio)
    return portfolios


@pytest.fixture
def test_metrics_service(db: Session):
    """Create metrics service."""
    return PortfolioUpdateMetricsService(db)


class TestPortfolioUpdateMetrics:
    """Test portfolio update metrics collection and reporting."""

    def test_record_portfolio_update_metrics(self, db: Session, test_portfolios, test_metrics_service):
        """Test recording portfolio update metrics."""
        portfolio = test_portfolios[0]

        # Record a successful update
        start_time = datetime.utcnow()
        metrics = test_metrics_service.record_portfolio_update(
            portfolio_id=str(portfolio.id),
            symbols_updated=["AAPL", "GOOGL"],
            update_duration_ms=150,
            status="success",
            trigger_type="market_data_change",
            update_source="automated"
        )

        # Verify metrics were recorded
        assert metrics is not None
        assert metrics.portfolio_id == str(portfolio.id)
        assert metrics.symbols_count == 2
        assert metrics.update_duration_ms == 150
        assert metrics.status == "success"
        assert metrics.trigger_type == "market_data_change"
        assert metrics.update_source == "automated"
        assert metrics.created_at >= start_time

    def test_record_queue_metrics(self, db: Session, test_metrics_service):
        """Test recording portfolio update queue metrics."""
        # Mock queue stats
        queue_stats = {
            "pending_updates": 15,
            "portfolio_symbol_counts": {"portfolio-1": 3, "portfolio-2": 2},
            "rate_limit_windows": {"portfolio-1": 2, "portfolio-2": 1},
            "is_processing": True,
            "debounce_seconds": 2.0,
            "max_updates_per_minute": 20
        }

        metrics = test_metrics_service.record_queue_metrics(
            pending_updates=queue_stats["pending_updates"],
            processing_rate=12.5,  # updates per minute
            active_portfolios=len(queue_stats["portfolio_symbol_counts"]),
            rate_limit_hits=sum(queue_stats["rate_limit_windows"].values()),
            memory_usage_mb=45.2
        )

        # Verify queue metrics were recorded
        assert metrics is not None
        assert metrics.pending_updates == 15
        assert float(metrics.processing_rate) == 12.5
        assert metrics.active_portfolios == 2
        assert metrics.rate_limit_hits == 3
        assert float(metrics.memory_usage_mb) == 45.2

    def test_get_portfolio_update_stats_24h(self, db: Session, test_portfolios, test_metrics_service):
        """Test getting 24-hour portfolio update statistics."""
        portfolio = test_portfolios[0]

        # Record several updates over time
        base_time = datetime.utcnow() - timedelta(hours=2)

        # Successful updates
        for i in range(10):
            test_metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=["AAPL"],
                update_duration_ms=100 + i * 10,  # Varying durations
                status="success",
                trigger_type="market_data_change",
                update_source="automated",
                created_at=base_time + timedelta(minutes=i * 10)
            )

        # Some failed updates
        for i in range(2):
            test_metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=["GOOGL"],
                update_duration_ms=0,
                status="error",
                trigger_type="market_data_change",
                update_source="automated",
                error_message="Rate limit exceeded",
                created_at=base_time + timedelta(minutes=(i + 10) * 10)
            )

        # Get 24-hour stats
        stats = test_metrics_service.get_portfolio_update_stats_24h()

        # Verify statistics
        assert stats["total_updates"] == 12
        assert stats["successful_updates"] == 10
        assert stats["failed_updates"] == 2
        assert stats["success_rate"] == pytest.approx(83.3, rel=0.1)
        assert stats["avg_update_duration_ms"] > 0
        assert stats["unique_portfolios"] >= 1
        assert "update_frequency_per_hour" in stats
        assert "common_error_types" in stats

    def test_get_queue_health_metrics(self, db: Session, test_metrics_service):
        """Test getting queue health metrics."""
        # Record queue metrics over time
        base_time = datetime.utcnow() - timedelta(hours=1)

        for i in range(6):  # Record every 10 minutes for 1 hour
            test_metrics_service.record_queue_metrics(
                pending_updates=5 + i,  # Increasing backlog
                processing_rate=10.0 + i * 2,  # Increasing processing rate
                active_portfolios=3,
                rate_limit_hits=i,  # Increasing rate limits
                memory_usage_mb=40.0 + i * 2,
                created_at=base_time + timedelta(minutes=i * 10)
            )

        # Get health metrics
        health = test_metrics_service.get_queue_health_metrics()

        # Verify health metrics
        assert health["current_queue_size"] >= 0
        assert health["avg_processing_rate"] > 0
        assert health["max_queue_size_1h"] >= health["current_queue_size"]
        assert health["rate_limit_hits_1h"] >= 0
        assert health["memory_usage_trend"] in ["increasing", "decreasing", "stable"]
        assert health["queue_health_status"] in ["healthy", "warning", "critical"]

    def test_get_storm_protection_metrics(self, db: Session, test_portfolios, test_metrics_service):
        """Test getting update storm protection effectiveness metrics."""
        # Simulate storm protection scenarios
        portfolio = test_portfolios[0]

        # Record coalescing events (multiple symbols updated together)
        test_metrics_service.record_portfolio_update(
            portfolio_id=str(portfolio.id),
            symbols_updated=["AAPL", "GOOGL", "MSFT", "TSLA"],  # 4 symbols coalesced
            update_duration_ms=200,
            status="success",
            trigger_type="bulk_market_data",
            update_source="automated",
            coalesced_count=4  # 4 individual updates became 1
        )

        # Record some individual updates
        for symbol in ["AMZN", "META", "NVDA"]:
            test_metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=[symbol],
                update_duration_ms=120,
                status="success",
                trigger_type="market_data_change",
                update_source="automated"
            )

        # Get storm protection metrics
        storm_metrics = test_metrics_service.get_storm_protection_metrics()

        # Verify storm protection effectiveness
        assert storm_metrics["total_coalesced_updates"] >= 1
        assert storm_metrics["total_individual_updates"] >= 3
        assert storm_metrics["coalescing_efficiency"] > 0  # Percentage of updates that were coalesced
        assert storm_metrics["avg_symbols_per_update"] > 1
        assert storm_metrics["storm_events_detected"] >= 0
        assert storm_metrics["protection_effectiveness"] >= 0  # Percentage of load reduction

    def test_get_portfolio_performance_breakdown(self, db: Session, test_portfolios, test_metrics_service):
        """Test getting per-portfolio performance breakdown."""
        # Record updates for different portfolios
        for i, portfolio in enumerate(test_portfolios[:3]):
            # Different performance patterns per portfolio
            update_count = (i + 1) * 5
            avg_duration = 100 + i * 50

            for j in range(update_count):
                test_metrics_service.record_portfolio_update(
                    portfolio_id=str(portfolio.id),
                    symbols_updated=["AAPL"],
                    update_duration_ms=avg_duration + j * 10,
                    status="success" if j < update_count - 1 else "error",  # Last one fails
                    trigger_type="market_data_change",
                    update_source="automated"
                )

        # Get performance breakdown
        breakdown = test_metrics_service.get_portfolio_performance_breakdown(limit=5)

        # Verify breakdown
        assert len(breakdown) >= 3
        for item in breakdown:
            assert "portfolio_id" in item
            assert "portfolio_name" in item
            assert "total_updates" in item
            assert "success_rate" in item
            assert "avg_duration_ms" in item
            assert "last_updated" in item

    def test_get_update_lag_analysis(self, db: Session, test_portfolios, test_metrics_service):
        """Test getting update lag analysis (time from price change to portfolio update)."""
        portfolio = test_portfolios[0]

        # Record updates with different lag times
        base_time = datetime.utcnow()

        for i in range(10):
            # Simulate different lag times (0.5s to 5s)
            lag_ms = 500 + i * 450

            test_metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=["AAPL"],
                update_duration_ms=100,
                status="success",
                trigger_type="market_data_change",
                update_source="automated",
                price_change_timestamp=base_time - timedelta(milliseconds=lag_ms),
                created_at=base_time
            )
            base_time += timedelta(minutes=1)

        # Get lag analysis
        lag_analysis = test_metrics_service.get_update_lag_analysis()

        # Verify lag analysis
        assert lag_analysis["avg_lag_ms"] > 0
        assert lag_analysis["median_lag_ms"] > 0
        assert lag_analysis["p95_lag_ms"] > lag_analysis["median_lag_ms"]
        assert lag_analysis["max_lag_ms"] >= lag_analysis["p95_lag_ms"]
        assert lag_analysis["samples_analyzed"] == 10
        assert lag_analysis["lag_distribution"]["0-1s"] >= 0
        assert lag_analysis["lag_distribution"]["1-5s"] >= 0
        assert lag_analysis["lag_distribution"]["5s+"] >= 0

    def test_export_metrics_for_monitoring(self, db: Session, test_portfolios, test_metrics_service):
        """Test exporting metrics in format suitable for external monitoring tools."""
        portfolio = test_portfolios[0]

        # Record some metrics
        test_metrics_service.record_portfolio_update(
            portfolio_id=str(portfolio.id),
            symbols_updated=["AAPL", "GOOGL"],
            update_duration_ms=150,
            status="success",
            trigger_type="market_data_change",
            update_source="automated"
        )

        test_metrics_service.record_queue_metrics(
            pending_updates=5,
            processing_rate=12.0,
            active_portfolios=2,
            rate_limit_hits=1,
            memory_usage_mb=42.0
        )

        # Export metrics
        exported = test_metrics_service.export_metrics_for_monitoring()

        # Verify exported format (Prometheus-style metrics)
        assert "portfolio_updates_total" in exported
        assert "portfolio_updates_duration_seconds" in exported
        assert "portfolio_queue_pending_updates" in exported
        assert "portfolio_queue_processing_rate" in exported
        assert "portfolio_update_success_rate" in exported

        # Should include help text and type information
        for metric in exported:
            assert "# HELP" in exported[metric]
            assert "# TYPE" in exported[metric]

    @patch('src.services.portfolio_update_queue.get_portfolio_update_queue')
    def test_collect_live_queue_metrics(self, mock_get_queue, db: Session, test_metrics_service):
        """Test collecting live metrics from the portfolio update queue."""
        # Mock the queue
        mock_queue = MagicMock()
        mock_queue.get_queue_stats.return_value = {
            "pending_updates": 8,
            "portfolio_symbol_counts": {"p1": 2, "p2": 3, "p3": 1},
            "rate_limit_windows": {"p1": 1, "p2": 0, "p3": 2},
            "is_processing": True,
            "debounce_seconds": 2.0,
            "max_updates_per_minute": 20
        }
        mock_get_queue.return_value = mock_queue

        # Collect live metrics
        live_metrics = test_metrics_service.collect_live_queue_metrics()

        # Verify live metrics collection
        assert live_metrics["pending_updates"] == 8
        assert live_metrics["active_portfolios"] == 3
        assert live_metrics["rate_limit_hits"] == 3
        assert live_metrics["is_processing"] is True
        assert live_metrics["total_symbols_queued"] == 6

    def test_metrics_cleanup_old_data(self, db: Session, test_metrics_service):
        """Test cleanup of old metrics data to prevent database bloat."""
        # Record old metrics (older than retention period)
        old_time = datetime.utcnow() - timedelta(days=35)  # Older than 30-day retention

        test_metrics_service.record_portfolio_update(
            portfolio_id="old-portfolio",
            symbols_updated=["OLD"],
            update_duration_ms=100,
            status="success",
            trigger_type="market_data_change",
            update_source="automated",
            created_at=old_time
        )

        test_metrics_service.record_queue_metrics(
            pending_updates=1,
            processing_rate=1.0,
            active_portfolios=1,
            rate_limit_hits=0,
            memory_usage_mb=30.0,
            created_at=old_time
        )

        # Run cleanup
        cleaned_update_records = test_metrics_service.cleanup_old_metrics(retention_days=30)
        cleaned_queue_records = test_metrics_service.cleanup_old_queue_metrics(retention_days=30)

        # Verify cleanup
        assert cleaned_update_records >= 1
        assert cleaned_queue_records >= 1

        # Verify old data is gone
        recent_stats = test_metrics_service.get_portfolio_update_stats_24h()
        # Should not include the old update in recent stats
        assert recent_stats["total_updates"] == 0
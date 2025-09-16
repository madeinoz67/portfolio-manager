"""
Test-driven development tests for timezone handling in database models.

Tests that all models use local time instead of UTC for timestamp fields.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.stock import Stock
from src.models.transaction import Transaction
from src.models.api_key import ApiKey
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.market_data_provider import MarketDataProvider
from src.models.news_notice import NewsNotice
from src.models.poll_interval_config import PollIntervalConfig
from src.models.portfolio_valuation import PortfolioValuation
from src.models.price_history import PriceHistory
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.sse_connection import SSEConnection
from src.models.user_role import UserRole
from src.utils.datetime_utils import now


class TestTimezoneHandling:
    """Test that all models use local time instead of UTC."""

    @pytest.fixture
    def mock_local_time(self):
        """Mock the local time function to return a known datetime."""
        local_datetime = datetime(2025, 9, 14, 15, 30, 45)  # Local time
        with patch('src.utils.datetime_utils.now', return_value=local_datetime):
            yield local_datetime

    def test_user_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test User model uses local time for timestamps."""
        user = User(
            email="test@example.com",
            password_hash="test_hash",
            first_name="Test",
            last_name="User"
        )

        db_session.add(user)
        db_session.commit()

        # Verify created_at and updated_at use local time
        assert user.created_at == mock_local_time
        assert user.updated_at == mock_local_time

    def test_portfolio_timestamps_use_local_time(self, db_session: Session, test_data, mock_local_time):
        """Test Portfolio model uses local time for timestamps."""
        portfolio = Portfolio(
            name="Test Portfolio",
            description="Test description",
            owner_id=test_data.user.id
        )

        db_session.add(portfolio)
        db_session.commit()

        # Verify timestamps use local time
        assert portfolio.created_at == mock_local_time
        assert portfolio.updated_at == mock_local_time

    def test_holding_timestamps_use_local_time(self, db_session: Session, test_data, mock_local_time):
        """Test Holding model uses local time for timestamps."""
        holding = Holding(
            portfolio_id=test_data.portfolio.id,
            stock_id=test_data.stock.id,
            quantity=100.0,
            average_cost=50.0
        )

        db_session.add(holding)
        db_session.commit()

        # Verify timestamps use local time
        assert holding.created_at == mock_local_time
        assert holding.updated_at == mock_local_time

    def test_stock_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test Stock model uses local time for timestamps."""
        stock = Stock(
            symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            current_price=150.00
        )

        db_session.add(stock)
        db_session.commit()

        # Verify timestamps use local time
        assert stock.created_at == mock_local_time
        assert stock.updated_at == mock_local_time

    def test_transaction_timestamps_use_local_time(self, db_session: Session, sample_portfolio, sample_stock, mock_local_time):
        """Test Transaction model uses local time for timestamps."""
        from src.models.transaction import TransactionType

        transaction = Transaction(
            portfolio_id=sample_portfolio.id,
            stock_id=sample_stock.id,
            type=TransactionType.BUY,
            quantity=50.0,
            price=100.0
        )

        db_session.add(transaction)
        db_session.commit()

        # Verify processed_date uses local time
        assert transaction.processed_date == mock_local_time

    def test_api_key_timestamps_use_local_time(self, db_session: Session, sample_user, mock_local_time):
        """Test ApiKey model uses local time for timestamps."""
        api_key = ApiKey(
            user_id=sample_user.id,
            name="Test API Key",
            key_hash="test_key_hash"
        )

        db_session.add(api_key)
        db_session.commit()

        # Verify created_at uses local time
        assert api_key.created_at == mock_local_time

    def test_api_usage_metrics_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test MarketDataUsageMetrics model uses local time for timestamps."""
        metrics = MarketDataUsageMetrics(
            metric_id="test_metric",
            provider_id="alpha_vantage",
            request_type="stock_quote",
            time_bucket="15min",
            requests_count=5,
            data_points_fetched=100
        )

        db_session.add(metrics)
        db_session.commit()

        # Verify recorded_at uses local time
        assert metrics.recorded_at == mock_local_time

    def test_market_data_provider_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test MarketDataProvider model uses local time for timestamps."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            api_endpoint="https://api.test.com",
            is_enabled=True,
            rate_limit_per_day=1000,
            cost_per_request=0.01
        )

        db_session.add(provider)
        db_session.commit()

        # Verify timestamps use local time
        assert provider.created_at == mock_local_time
        assert provider.updated_at == mock_local_time

    def test_news_notice_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test NewsNotice model uses local time for timestamps."""
        news = NewsNotice(
            title="Test News",
            content="Test content",
            category="general",
            priority="medium",
            is_active=True
        )

        db_session.add(news)
        db_session.commit()

        # Verify timestamps use local time
        assert news.created_at == mock_local_time
        assert news.updated_at == mock_local_time

    def test_poll_interval_config_timestamps_use_local_time(self, db_session: Session, mock_local_time):
        """Test PollIntervalConfig model uses local time for timestamps."""
        config = PollIntervalConfig(
            provider_name="test_provider",
            interval_seconds=900,
            is_enabled=True
        )

        db_session.add(config)
        db_session.commit()

        # Verify created_at uses local time
        assert config.created_at == mock_local_time

    def test_portfolio_valuation_timestamps_use_local_time(self, db_session: Session, sample_portfolio, mock_local_time):
        """Test PortfolioValuation model uses local time for timestamps."""
        valuation = PortfolioValuation(
            portfolio_id=sample_portfolio.id,
            total_value=1000.00,
            ttl_minutes=20
        )

        db_session.add(valuation)
        db_session.commit()

        # Verify timestamps use local time
        assert valuation.calculated_at == mock_local_time
        assert valuation.created_at == mock_local_time

    def test_price_history_timestamps_use_local_time(self, db_session: Session, sample_stock, mock_local_time):
        """Test PriceHistory model uses local time for timestamps."""
        price_history = PriceHistory(
            stock_id=sample_stock.id,
            price=150.00,
            volume=1000000,
            date=datetime.now().date()
        )

        db_session.add(price_history)
        db_session.commit()

        # Verify created_at uses local time
        assert price_history.created_at == mock_local_time

    def test_realtime_price_history_timestamps_use_local_time(self, db_session: Session, sample_stock, mock_local_time):
        """Test RealtimePriceHistory model uses local time for timestamps."""
        realtime_price = RealtimePriceHistory(
            stock_id=sample_stock.id,
            price=151.00,
            volume=50000,
            provider_id="alpha_vantage"
        )

        db_session.add(realtime_price)
        db_session.commit()

        # Verify timestamps use local time
        assert realtime_price.fetched_at == mock_local_time
        assert realtime_price.created_at == mock_local_time

    def test_sse_connection_timestamps_use_local_time(self, db_session: Session, sample_user, mock_local_time):
        """Test SSEConnection model uses local time for timestamps."""
        connection = SSEConnection(
            user_id=sample_user.id,
            connection_id="test_connection",
            topic="portfolio_updates",
            is_active=True
        )

        db_session.add(connection)
        db_session.commit()

        # Verify timestamps use local time
        assert connection.connected_at == mock_local_time
        assert connection.created_at == mock_local_time

    def test_datetime_utils_now_returns_local_time(self):
        """Test that the now() utility function returns local time, not UTC."""
        local_time = now()
        utc_time = datetime.utcnow()

        # The local time should be different from UTC (unless running in UTC timezone)
        # We check that it's a datetime object and not explicitly UTC
        assert isinstance(local_time, datetime)
        assert local_time.tzinfo is None  # Should be naive local time

        # Verify it's actually local time by checking it's reasonable
        import time
        local_offset = time.timezone if time.daylight == 0 else time.altzone
        expected_diff = abs(local_offset) / 3600  # Convert to hours

        # The difference between our local time and UTC should match system timezone
        time_diff = abs((local_time - utc_time).total_seconds() / 3600)
        assert time_diff <= expected_diff + 1  # Allow 1 hour tolerance

    def test_updated_models_dont_use_datetime_utcnow(self):
        """Test that updated models don't import or use datetime.utcnow directly."""
        import inspect

        models_to_check = [
            User, Portfolio, Holding, Stock, Transaction, ApiKey,
            MarketDataUsageMetrics, MarketDataProvider, NewsNotice, PollIntervalConfig,
            PortfolioValuation, PriceHistory, RealtimePriceHistory, SSEConnection
        ]

        for model_class in models_to_check:
            # Get the source code of the model
            source = inspect.getsource(model_class)

            # Verify that datetime.utcnow is not used in the source
            assert "datetime.utcnow" not in source, f"Model {model_class.__name__} still uses datetime.utcnow"

            # Verify that 'now' from datetime_utils is imported and used
            if hasattr(model_class, '__table__'):
                # Check if any datetime columns exist
                has_datetime_columns = any(
                    str(col.type).startswith('DATETIME')
                    for col in model_class.__table__.columns
                )

                if has_datetime_columns:
                    # Should import from datetime_utils
                    assert "from src.utils.datetime_utils import now" in source, \
                        f"Model {model_class.__name__} should import 'now' from datetime_utils"

    def test_logging_uses_local_time(self):
        """Test that logging timestamps use local time instead of UTC."""
        from src.core.logging import StructuredFormatter
        import logging

        formatter = StructuredFormatter()

        # Create a mock log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # Format the record
        formatted = formatter.format(record)

        # Parse the JSON to check the timestamp
        import json
        log_data = json.loads(formatted)

        # Verify timestamp is present and in local time format
        assert "timestamp" in log_data
        timestamp_str = log_data["timestamp"]

        # Parse the timestamp
        parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00') if timestamp_str.endswith('Z') else timestamp_str)

        # Should not end with Z (UTC indicator)
        assert not timestamp_str.endswith('Z'), "Logging timestamp should not be UTC (ending with Z)"

        # Should be close to current local time
        current_time = now()
        time_diff = abs((parsed_timestamp.replace(tzinfo=None) - current_time).total_seconds())
        assert time_diff < 60, "Log timestamp should be close to current local time"
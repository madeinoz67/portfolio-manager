"""
Functional tests to verify timezone changes work correctly.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.user import User
from src.models.market_data_api_usage_metrics import ApiUsageMetrics
from src.utils.datetime_utils import now, utc_now


class TestTimezoneFunctional:
    """Functional tests to verify timezone behavior."""

    def test_datetime_utils_local_vs_utc(self):
        """Test that now() returns local time and utc_now() returns UTC."""
        local_time = now()
        utc_time = utc_now()

        # Both should be datetime objects
        assert isinstance(local_time, datetime)
        assert isinstance(utc_time, datetime)

        # Local time should be naive (no timezone)
        assert local_time.tzinfo is None

        # UTC time should have timezone info
        assert utc_time.tzinfo is not None
        assert utc_time.tzinfo == timezone.utc

    def test_user_model_uses_local_time(self, db_session: Session):
        """Test that User model creates timestamps in local time."""
        # Record time before creating user
        before_time = now()

        user = User(
            email="test@example.com",
            password_hash="test_hash",
            first_name="Test",
            last_name="User"
        )

        db_session.add(user)
        db_session.commit()

        # Record time after creating user
        after_time = now()

        # User timestamps should be between before and after
        assert before_time <= user.created_at <= after_time
        assert before_time <= user.updated_at <= after_time

        # Should be local time (naive datetime)
        assert user.created_at.tzinfo is None
        assert user.updated_at.tzinfo is None

    def test_api_usage_metrics_uses_local_time(self, db_session: Session):
        """Test that ApiUsageMetrics model creates timestamps in local time."""
        before_time = now()

        metrics = ApiUsageMetrics(
            metric_id="test_metric",
            provider_id="alpha_vantage",
            request_type="stock_quote",
            time_bucket="15min",
            requests_count=5
        )

        db_session.add(metrics)
        db_session.commit()

        after_time = now()

        # Timestamp should be between before and after
        assert before_time <= metrics.recorded_at <= after_time

        # Should be local time (naive datetime)
        assert metrics.recorded_at.tzinfo is None

    def test_models_no_longer_use_datetime_utcnow(self):
        """Test that updated models don't use datetime.utcnow directly."""
        import inspect
        from src.models import user, api_usage_metrics, portfolio, holding

        # Get source code for key models
        models_to_check = [user, api_usage_metrics, portfolio, holding]

        for model_module in models_to_check:
            source = inspect.getsource(model_module)

            # Should not contain datetime.utcnow
            assert "datetime.utcnow" not in source, f"Module {model_module.__name__} still uses datetime.utcnow"

            # Should import from datetime_utils if it has datetime columns
            if hasattr(model_module, 'User') or hasattr(model_module, 'ApiUsageMetrics') or hasattr(model_module, 'Portfolio') or hasattr(model_module, 'Holding'):
                assert "from src.utils.datetime_utils import now" in source, f"Module {model_module.__name__} should import 'now' from datetime_utils"

    def test_timezone_difference_validation(self):
        """Test that local time and UTC time show expected difference."""
        local_time = now()
        utc_time = utc_now().replace(tzinfo=None)  # Make naive for comparison

        # Calculate difference (should match system timezone offset)
        time_diff_hours = abs((local_time - utc_time).total_seconds() / 3600)

        # Should be reasonable timezone difference (0-12 hours typically)
        assert 0 <= time_diff_hours <= 12, f"Unexpected time difference: {time_diff_hours} hours"

    def test_logging_timestamp_format(self):
        """Test that logging uses local time format."""
        from src.core.logging import StructuredFormatter
        import logging
        import json

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test timezone message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        # Should have timestamp field
        assert "timestamp" in log_data
        timestamp_str = log_data["timestamp"]

        # Should not end with 'Z' (UTC marker)
        assert not timestamp_str.endswith('Z'), "Log timestamp should not be UTC"

        # Should be parseable as ISO format
        parsed_timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_timestamp, datetime)

    def test_model_import_consistency(self):
        """Test that all updated models consistently import datetime utilities."""
        import inspect
        from src.models import (
            user, portfolio, holding, stock, transaction, api_key,
            api_usage_metrics, market_data_provider, news_notice,
            poll_interval_config, portfolio_valuation, price_history,
            realtime_price_history, sse_connection
        )

        models_with_datetime = [
            user, portfolio, holding, stock, transaction, api_key,
            api_usage_metrics, market_data_provider, news_notice,
            poll_interval_config, portfolio_valuation, price_history,
            realtime_price_history, sse_connection
        ]

        for model_module in models_with_datetime:
            source = inspect.getsource(model_module)

            # Should import datetime_utils
            assert "from src.utils.datetime_utils import now" in source, \
                f"Model {model_module.__name__} should import 'now' from datetime_utils"

            # Should not use datetime.utcnow
            assert "datetime.utcnow" not in source, \
                f"Model {model_module.__name__} should not use datetime.utcnow"
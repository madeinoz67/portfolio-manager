"""
TDD tests for trend fallback behavior when opening price data is missing.

Tests that the system displays neutral trends (0%) when insufficient data
is available for proper trend calculation.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.services.trend_calculation_service import TrendCalculationService, PriceTrend
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.api.market_data import build_price_response, TrendData
from src.utils.datetime_utils import utc_now


class TestTrendFallbackBehavior:
    """Test suite for trend fallback behavior with missing data."""

    @pytest.fixture
    def trend_service(self, db_session: Session):
        """Create trend calculation service."""
        return TrendCalculationService(db_session)

    @pytest.fixture
    def sample_provider(self, db_session: Session):
        """Create sample market data provider."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            is_enabled=True,
            priority=1,
            rate_limit_per_day=1000
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    def test_fallback_neutral_trend_no_opening_price(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test that neutral trend (0%) is returned when no opening price is available."""
        symbol = "BHP"
        current_price = Decimal("40.50")

        # Add only current price, no opening price
        current_time = utc_now()
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=None  # No opening price data
        )
        db_session.add(price_record)
        db_session.commit()

        # Trend calculation should return None when no opening price available
        trend_data = trend_service.calculate_trend(symbol)
        assert trend_data is None

        # But build_price_response should provide fallback neutral trend
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=False,
            trend_service=trend_service
        )

        # Should have neutral trend fallback
        assert response.trend is not None
        assert response.trend.trend == "neutral"
        assert response.trend.change == 0.0
        assert response.trend.change_percent == 0.0
        assert response.trend.opening_price is None

    def test_fallback_neutral_trend_no_service(self, sample_provider: MarketDataProvider, db_session: Session):
        """Test that neutral trend is returned when no trend service is provided."""
        symbol = "WBC"
        current_price = Decimal("25.80")

        current_time = utc_now()
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=500000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=Decimal("25.50")  # Even with opening price
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response without trend service
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=True,
            trend_service=None  # No trend service provided
        )

        # Should still have neutral trend fallback
        assert response.trend is not None
        assert response.trend.trend == "neutral"
        assert response.trend.change == 0.0
        assert response.trend.change_percent == 0.0
        assert response.trend.opening_price is None

    def test_actual_trend_when_data_available(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test that actual trend is returned when sufficient data is available."""
        symbol = "CSL"
        opening_price = Decimal("280.00")
        current_price = Decimal("285.50")

        current_time = utc_now()
        price_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=750000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=opening_price
        )
        db_session.add(price_record)
        db_session.commit()

        # Build response with trend service and data
        response = build_price_response(
            symbol=symbol,
            price_record=price_record,
            cached=False,
            trend_service=trend_service
        )

        # Should have actual trend data (up trend)
        assert response.trend is not None
        assert response.trend.trend == "up"
        assert response.trend.change == 5.5  # 285.50 - 280.00
        assert response.trend.change_percent == 1.96  # Approximately (5.5/280)*100
        assert response.trend.opening_price == 280.00

    def test_multiple_symbols_mixed_data_availability(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test multiple symbols with mixed data availability."""
        symbols_data = [
            ("ANZ", Decimal("22.50"), None),  # No opening price
            ("NAB", Decimal("28.80"), Decimal("28.70")),  # Has opening price
            ("MQG", Decimal("165.40"), None),  # No opening price
        ]

        current_time = utc_now()
        responses = []

        for symbol, current_price, opening_price in symbols_data:
            price_record = RealtimePriceHistory(
                symbol=symbol,
                price=current_price,
                volume=100000,
                provider_id=sample_provider.id,
                source_timestamp=current_time,
                opening_price=opening_price
            )
            db_session.add(price_record)

        db_session.commit()

        # Build responses for all symbols
        for symbol, current_price, opening_price in symbols_data:
            price_record = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol).first()
            response = build_price_response(
                symbol=symbol,
                price_record=price_record,
                cached=False,
                trend_service=trend_service
            )
            responses.append(response)

        # Check responses
        # ANZ - should have neutral fallback (no opening price)
        anz_response = responses[0]
        assert anz_response.trend.trend == "neutral"
        assert anz_response.trend.change == 0.0
        assert anz_response.trend.change_percent == 0.0

        # NAB - should have actual up trend
        nab_response = responses[1]
        assert nab_response.trend.trend == "up"
        assert nab_response.trend.change == 0.1  # 28.80 - 28.70
        assert abs(nab_response.trend.change_percent - 0.35) < 0.01  # Approximately 0.35%

        # MQG - should have neutral fallback (no opening price)
        mqg_response = responses[2]
        assert mqg_response.trend.trend == "neutral"
        assert mqg_response.trend.change == 0.0
        assert mqg_response.trend.change_percent == 0.0
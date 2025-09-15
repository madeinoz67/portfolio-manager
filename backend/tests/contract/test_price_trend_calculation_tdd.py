"""
TDD tests for price trend calculation functionality.

Tests the calculation of price trends (up, down, neutral) and percentage changes
by comparing current prices to opening prices for each trading day.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.services.trend_calculation_service import TrendCalculationService, PriceTrend
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.utils.datetime_utils import utc_now


class TestPriceTrendCalculation:
    """Test suite for price trend calculation logic."""

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

    def test_trend_calculation_price_up(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test trend calculation when current price is higher than opening price."""
        symbol = "AAPL"
        opening_price = Decimal("150.00")
        current_price = Decimal("155.00")

        # Add opening price (market open time)
        market_open = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)  # 9:30 AM EST
        opening_record = RealtimePriceHistory(
            symbol=symbol,
            price=opening_price,
            volume=1000000,
            provider_id=sample_provider.id,
            source_timestamp=market_open,
            opening_price=opening_price
        )
        db_session.add(opening_record)

        # Add current price
        current_time = market_open + timedelta(hours=2)
        current_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=1200000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=opening_price
        )
        db_session.add(current_record)
        db_session.commit()

        # Calculate trend
        trend_data = trend_service.calculate_trend(symbol)

        # Assertions
        assert trend_data is not None
        assert trend_data.symbol == symbol
        assert trend_data.current_price == current_price
        assert trend_data.opening_price == opening_price
        assert trend_data.trend == PriceTrend.UP
        assert trend_data.change == Decimal("5.00")
        assert trend_data.change_percent == Decimal("3.33")  # (5/150) * 100 = 3.33%

    def test_trend_calculation_price_down(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test trend calculation when current price is lower than opening price."""
        symbol = "TSLA"
        opening_price = Decimal("800.00")
        current_price = Decimal("780.00")

        # Add opening price
        market_open = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)
        opening_record = RealtimePriceHistory(
            symbol=symbol,
            price=opening_price,
            volume=500000,
            provider_id=sample_provider.id,
            source_timestamp=market_open,
            opening_price=opening_price
        )
        db_session.add(opening_record)

        # Add current price
        current_time = market_open + timedelta(hours=3)
        current_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=750000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=opening_price
        )
        db_session.add(current_record)
        db_session.commit()

        # Calculate trend
        trend_data = trend_service.calculate_trend(symbol)

        # Assertions
        assert trend_data is not None
        assert trend_data.symbol == symbol
        assert trend_data.current_price == current_price
        assert trend_data.opening_price == opening_price
        assert trend_data.trend == PriceTrend.DOWN
        assert trend_data.change == Decimal("-20.00")
        assert trend_data.change_percent == Decimal("-2.50")  # (-20/800) * 100 = -2.5%

    def test_trend_calculation_price_neutral(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test trend calculation when current price equals opening price."""
        symbol = "GOOGL"
        opening_price = Decimal("2500.00")
        current_price = Decimal("2500.00")

        # Add opening price
        market_open = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)
        opening_record = RealtimePriceHistory(
            symbol=symbol,
            price=opening_price,
            volume=100000,
            provider_id=sample_provider.id,
            source_timestamp=market_open,
            opening_price=opening_price
        )
        db_session.add(opening_record)

        # Add current price (same as opening)
        current_time = market_open + timedelta(hours=1)
        current_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=110000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=opening_price
        )
        db_session.add(current_record)
        db_session.commit()

        # Calculate trend
        trend_data = trend_service.calculate_trend(symbol)

        # Assertions
        assert trend_data is not None
        assert trend_data.symbol == symbol
        assert trend_data.current_price == current_price
        assert trend_data.opening_price == opening_price
        assert trend_data.trend == PriceTrend.NEUTRAL
        assert trend_data.change == Decimal("0.00")
        assert trend_data.change_percent == Decimal("0.00")

    def test_trend_calculation_no_opening_price(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test trend calculation when no opening price is available."""
        symbol = "MSFT"
        current_price = Decimal("300.00")

        # Add only current price, no opening price
        current_time = utc_now()
        current_record = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            volume=800000,
            provider_id=sample_provider.id,
            source_timestamp=current_time,
            opening_price=None
        )
        db_session.add(current_record)
        db_session.commit()

        # Calculate trend should return None when no opening price available
        trend_data = trend_service.calculate_trend(symbol)

        assert trend_data is None

    def test_trend_calculation_multiple_symbols(self, trend_service: TrendCalculationService, sample_provider: MarketDataProvider, db_session: Session):
        """Test bulk trend calculation for multiple symbols."""
        symbols = ["AAPL", "TSLA", "GOOGL"]
        market_open = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)

        # Add data for multiple symbols
        test_data = [
            ("AAPL", Decimal("150.00"), Decimal("155.00")),  # Up
            ("TSLA", Decimal("800.00"), Decimal("780.00")),  # Down
            ("GOOGL", Decimal("2500.00"), Decimal("2500.00"))  # Neutral
        ]

        for symbol, opening, current in test_data:
            # Add opening price
            opening_record = RealtimePriceHistory(
                symbol=symbol,
                price=opening,
                volume=1000000,
                provider_id=sample_provider.id,
                source_timestamp=market_open,
                opening_price=opening
            )
            db_session.add(opening_record)

            # Add current price
            current_record = RealtimePriceHistory(
                symbol=symbol,
                price=current,
                volume=1200000,
                provider_id=sample_provider.id,
                source_timestamp=market_open + timedelta(hours=2),
                opening_price=opening
            )
            db_session.add(current_record)

        db_session.commit()

        # Calculate trends for all symbols
        trend_results = trend_service.calculate_trends(symbols)

        # Verify results
        assert len(trend_results) == 3

        aapl_trend = next(t for t in trend_results if t.symbol == "AAPL")
        assert aapl_trend.trend == PriceTrend.UP
        assert aapl_trend.change_percent == Decimal("3.33")

        tsla_trend = next(t for t in trend_results if t.symbol == "TSLA")
        assert tsla_trend.trend == PriceTrend.DOWN
        assert tsla_trend.change_percent == Decimal("-2.50")

        googl_trend = next(t for t in trend_results if t.symbol == "GOOGL")
        assert googl_trend.trend == PriceTrend.NEUTRAL
        assert googl_trend.change_percent == Decimal("0.00")

    def test_percentage_calculation_precision(self, trend_service: TrendCalculationService):
        """Test that percentage calculations maintain proper precision."""
        # Test various price scenarios for precision
        test_cases = [
            (Decimal("100.00"), Decimal("100.01"), Decimal("0.01")),  # Small change
            (Decimal("1000.00"), Decimal("1003.33"), Decimal("0.33")),  # Fractional percentage
            (Decimal("50.00"), Decimal("55.55"), Decimal("11.10")),  # Double digits
            (Decimal("1.00"), Decimal("1.001"), Decimal("0.10")),  # Very small values
        ]

        for opening, current, expected_percent in test_cases:
            percentage = trend_service._calculate_percentage_change(opening, current)
            assert abs(percentage - expected_percent) < Decimal("0.01"), f"Expected {expected_percent}, got {percentage}"
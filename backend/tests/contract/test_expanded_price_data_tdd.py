"""
TDD tests for expanded price data storage functionality.

Tests the storage and retrieval of comprehensive price data including
opening prices, high/low prices, previous close, and all market data
from different providers to support trend calculations and analysis.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.services.market_data_service import MarketDataService
from src.utils.datetime_utils import utc_now


class TestExpandedPriceDataStorage:
    """Test suite for comprehensive price data storage and retrieval."""

    @pytest.fixture
    def market_data_service(self, db_session: Session):
        """Create market data service."""
        return MarketDataService(db_session)

    @pytest.fixture
    def yfinance_provider(self, db_session: Session):
        """Create yfinance provider."""
        provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1,
            rate_limit_per_day=1000
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    def test_store_comprehensive_price_data(self, market_data_service: MarketDataService, yfinance_provider: MarketDataProvider, db_session: Session):
        """Test storing all available price data fields from API response."""
        symbol = "AAPL"
        timestamp = utc_now()

        # Mock comprehensive price data from yfinance
        comprehensive_price_data = {
            "symbol": symbol,
            "price": Decimal("155.50"),           # Current price
            "open_price": Decimal("150.00"),      # Opening price for the day
            "high_price": Decimal("158.00"),      # Day's high
            "low_price": Decimal("149.50"),       # Day's low
            "previous_close": Decimal("151.25"),  # Previous day's close
            "volume": 12500000,                   # Trading volume
            "market_cap": 2450000000000,          # Market capitalization
            "fifty_two_week_high": Decimal("180.00"),  # 52-week high
            "fifty_two_week_low": Decimal("125.00"),   # 52-week low
            "dividend_yield": Decimal("0.56"),         # Dividend yield %
            "pe_ratio": Decimal("28.5"),              # Price-to-earnings ratio
            "beta": Decimal("1.25"),                  # Beta coefficient
            "currency": "USD",                        # Currency
            "company_name": "Apple Inc.",             # Company name
            "source_timestamp": timestamp,
            "provider": "yfinance"
        }

        # Store the comprehensive data
        stored_record = market_data_service._store_comprehensive_price_data(
            symbol, comprehensive_price_data, yfinance_provider, db_session
        )

        # Verify the record was created and stored correctly
        assert stored_record is not None
        assert stored_record.symbol == symbol
        assert stored_record.price == Decimal("155.50")
        assert stored_record.opening_price == Decimal("150.00")
        assert stored_record.high_price == Decimal("158.00")
        assert stored_record.low_price == Decimal("149.50")
        assert stored_record.previous_close == Decimal("151.25")
        assert stored_record.volume == 12500000
        assert stored_record.market_cap == Decimal("2450000000000")
        assert stored_record.fifty_two_week_high == Decimal("180.00")
        assert stored_record.fifty_two_week_low == Decimal("125.00")
        assert stored_record.dividend_yield == Decimal("0.56")
        assert stored_record.pe_ratio == Decimal("28.5")
        assert stored_record.beta == Decimal("1.25")
        assert stored_record.currency == "USD"
        assert stored_record.company_name == "Apple Inc."
        assert stored_record.provider_id == yfinance_provider.id

        # Verify data was persisted to database
        db_record = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol).first()
        assert db_record is not None
        assert db_record.opening_price == Decimal("150.00")
        assert db_record.high_price == Decimal("158.00")
        assert db_record.previous_close == Decimal("151.25")

    def test_opening_price_tracking_across_day(self, market_data_service: MarketDataService, yfinance_provider: MarketDataProvider, db_session: Session):
        """Test that opening prices are correctly maintained throughout the trading day."""
        symbol = "TSLA"
        base_date = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)  # 9:30 AM EST market open
        opening_price = Decimal("800.00")

        # Simulate price updates throughout the day - opening price should remain constant
        price_updates = [
            (base_date, Decimal("800.00")),                          # Market open
            (base_date + timedelta(hours=1), Decimal("805.50")),     # 1 hour later
            (base_date + timedelta(hours=3), Decimal("795.25")),     # 3 hours later
            (base_date + timedelta(hours=6), Decimal("810.75")),     # 6 hours later (market close)
        ]

        stored_records = []

        for timestamp, current_price in price_updates:
            price_data = {
                "symbol": symbol,
                "price": current_price,
                "open_price": opening_price,  # Opening price stays constant for the day
                "high_price": Decimal("815.00"),
                "low_price": Decimal("790.00"),
                "previous_close": Decimal("798.50"),
                "volume": 5000000,
                "market_cap": 750000000000,
                "source_timestamp": timestamp,
                "provider": "yfinance"
            }

            record = market_data_service._store_comprehensive_price_data(
                symbol, price_data, yfinance_provider, db_session
            )
            stored_records.append(record)

        # Verify all records have the same opening price
        for record in stored_records:
            assert record.opening_price == opening_price
            assert record.symbol == symbol
            assert record.provider_id == yfinance_provider.id

        # Verify database contains all records with consistent opening price
        db_records = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol).order_by(RealtimePriceHistory.source_timestamp).all()
        assert len(db_records) == 4

        for db_record in db_records:
            assert db_record.opening_price == opening_price

        # Verify prices changed but opening price remained constant
        prices = [record.price for record in db_records]
        assert prices == [Decimal("800.00"), Decimal("805.50"), Decimal("795.25"), Decimal("810.75")]

    def test_handle_missing_optional_fields(self, market_data_service: MarketDataService, yfinance_provider: MarketDataProvider, db_session: Session):
        """Test handling of API responses with missing optional fields."""
        symbol = "GOOGL"

        # Minimal price data (only required fields)
        minimal_price_data = {
            "symbol": symbol,
            "price": Decimal("2500.00"),
            "volume": 1000000,
            "source_timestamp": utc_now(),
            "provider": "yfinance"
            # Missing: opening_price, high_price, low_price, etc.
        }

        # Should handle missing fields gracefully
        stored_record = market_data_service._store_comprehensive_price_data(
            symbol, minimal_price_data, yfinance_provider, db_session
        )

        assert stored_record is not None
        assert stored_record.symbol == symbol
        assert stored_record.price == Decimal("2500.00")
        assert stored_record.volume == 1000000
        # Optional fields should be None
        assert stored_record.opening_price is None
        assert stored_record.high_price is None
        assert stored_record.low_price is None
        assert stored_record.previous_close is None
        assert stored_record.fifty_two_week_high is None
        assert stored_record.dividend_yield is None

    def test_retrieve_latest_opening_price(self, market_data_service: MarketDataService, yfinance_provider: MarketDataProvider, db_session: Session):
        """Test retrieving the latest opening price for trend calculations."""
        symbol = "MSFT"
        today = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0, microsecond=0)
        opening_price = Decimal("300.00")

        # Add multiple price records for the same day
        for i, hour_offset in enumerate([0, 1, 2, 3]):
            timestamp = today + timedelta(hours=hour_offset)
            current_price = opening_price + Decimal(str(i * 2))  # Price increases throughout day

            price_data = {
                "symbol": symbol,
                "price": current_price,
                "open_price": opening_price,  # Same opening price all day
                "volume": 1000000 + (i * 100000),
                "source_timestamp": timestamp,
                "provider": "yfinance"
            }

            market_data_service._store_comprehensive_price_data(
                symbol, price_data, yfinance_provider, db_session
            )

        # Test retrieval of opening price
        latest_opening_price = market_data_service.get_latest_opening_price(symbol)
        assert latest_opening_price == opening_price

        # Test retrieval of current price
        latest_current_price = market_data_service.get_latest_price_value(symbol)
        assert latest_current_price == opening_price + Decimal("6.00")  # Last price update

    def test_multiple_providers_same_symbol(self, market_data_service: MarketDataService, db_session: Session):
        """Test storing price data from multiple providers for the same symbol."""
        symbol = "BHP"
        timestamp = utc_now()

        # Create multiple providers
        yfinance_provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1,
            rate_limit_per_day=1000
        )

        alpha_vantage_provider = MarketDataProvider(
            name="alpha_vantage",
            display_name="Alpha Vantage",
            is_enabled=True,
            priority=2,
            rate_limit_per_day=500,
            api_key="test_key"
        )

        db_session.add(yfinance_provider)
        db_session.add(alpha_vantage_provider)
        db_session.commit()

        # Store price data from both providers
        yfinance_data = {
            "symbol": symbol,
            "price": Decimal("40.50"),
            "open_price": Decimal("40.00"),
            "volume": 5000000,
            "source_timestamp": timestamp,
            "provider": "yfinance"
        }

        alpha_vantage_data = {
            "symbol": symbol,
            "price": Decimal("40.52"),  # Slightly different price
            "open_price": Decimal("40.00"),  # Same opening price
            "volume": 5100000,
            "source_timestamp": timestamp + timedelta(minutes=1),
            "provider": "alpha_vantage"
        }

        yf_record = market_data_service._store_comprehensive_price_data(
            symbol, yfinance_data, yfinance_provider, db_session
        )

        av_record = market_data_service._store_comprehensive_price_data(
            symbol, alpha_vantage_data, alpha_vantage_provider, db_session
        )

        # Verify both records stored correctly
        assert yf_record.price == Decimal("40.50")
        assert av_record.price == Decimal("40.52")
        assert yf_record.opening_price == av_record.opening_price == Decimal("40.00")
        assert yf_record.provider_id == yfinance_provider.id
        assert av_record.provider_id == alpha_vantage_provider.id

        # Verify database contains both records
        db_records = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol).all()
        assert len(db_records) == 2

    def test_price_precision_handling(self, market_data_service: MarketDataService, yfinance_provider: MarketDataProvider, db_session: Session):
        """Test proper handling of decimal precision for financial data."""
        symbol = "CSL"

        # Test various price precision scenarios
        test_prices = [
            Decimal("207.8234"),    # 4 decimal places
            Decimal("207.82"),      # 2 decimal places
            Decimal("207.8"),       # 1 decimal place
            Decimal("207"),         # No decimal places
            Decimal("207.0000"),    # Trailing zeros
        ]

        for i, test_price in enumerate(test_prices):
            price_data = {
                "symbol": symbol,
                "price": test_price,
                "open_price": Decimal("205.00"),
                "volume": 100000,
                "source_timestamp": utc_now() + timedelta(minutes=i),
                "provider": "yfinance"
            }

            record = market_data_service._store_comprehensive_price_data(
                symbol, price_data, yfinance_provider, db_session
            )

            # Verify precision is maintained
            assert record.price == test_price
            assert record.opening_price == Decimal("205.00")

        # Verify all records persisted with correct precision
        db_records = db_session.query(RealtimePriceHistory).filter_by(symbol=symbol).order_by(RealtimePriceHistory.fetched_at).all()
        assert len(db_records) == len(test_prices)

        for i, db_record in enumerate(db_records):
            assert db_record.price == test_prices[i]
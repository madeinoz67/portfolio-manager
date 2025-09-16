"""
TDD test to verify opening_price fixes work properly.

This test directly checks that the yfinance integration improvements
can successfully retrieve opening_price data for Australian stocks.
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from src.services.market_data_service import MarketDataService
from src.models.market_data_provider import MarketDataProvider
from src.models.realtime_price_history import RealtimePriceHistory
from src.database import get_db
from sqlalchemy.orm import Session


@pytest.fixture
def market_data_service(db: Session):
    """Create MarketDataService with database session."""
    return MarketDataService(db)


@pytest.fixture
def yahoo_provider(db: Session):
    """Create and return a Yahoo Finance provider."""
    provider = MarketDataProvider(
        name="yfinance",
        display_name="Yahoo Finance",
        base_url="https://finance.yahoo.com",
        is_enabled=True,
        rate_limit_per_minute=60,
        config={}
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def test_opening_price_retrieval_for_australian_stocks(market_data_service, yahoo_provider):
    """Test that opening_price is properly retrieved for Australian stocks."""
    # Test CBA - Commonwealth Bank of Australia
    symbol = "CBA"

    # Mock yfinance ticker response with Australian stock data
    mock_ticker = Mock()
    mock_info = {
        'regularMarketPrice': 169.97,
        'open': 170.50,  # Opening price should be available
        'previousClose': 168.50,
        'currency': 'AUD',
        'longName': 'Commonwealth Bank of Australia'
    }
    mock_ticker.info = mock_info

    with patch('yfinance.Ticker', return_value=mock_ticker):
        # Call the service method
        result = market_data_service._fetch_price_from_yahoo(yahoo_provider, symbol)

        # Verify the result contains opening_price
        assert result is not None
        assert result.price == Decimal('169.97')
        assert result.opening_price == Decimal('170.50')  # This should NOT be None
        assert result.previous_close == Decimal('168.50')
        assert result.symbol == symbol


def test_opening_price_fallback_mechanisms(market_data_service, yahoo_provider):
    """Test that opening_price fallback mechanisms work correctly."""
    symbol = "CBA"

    # Test case 1: No opening price in regular info, should try .AX suffix
    mock_ticker_no_open = Mock()
    mock_ticker_no_open.info = {
        'regularMarketPrice': 169.97,
        'previousClose': 168.50,
        'currency': 'AUD'
        # No 'open' field
    }

    mock_ticker_with_ax = Mock()
    mock_ticker_with_ax.info = {
        'regularMarketPrice': 169.97,
        'open': 170.50,  # Available with .AX suffix
        'previousClose': 168.50,
        'currency': 'AUD'
    }

    def mock_ticker_factory(symbol_arg):
        if symbol_arg == "CBA.AX":
            return mock_ticker_with_ax
        return mock_ticker_no_open

    with patch('yfinance.Ticker', side_effect=mock_ticker_factory):
        result = market_data_service._fetch_price_from_yahoo(yahoo_provider, symbol)

        # Should successfully get opening_price from CBA.AX
        assert result is not None
        assert result.opening_price == Decimal('170.50')


def test_trend_calculation_with_opening_price(db: Session):
    """Test that trend calculation works correctly with opening_price data."""
    from src.services.trend_calculation_service import TrendCalculationService, PriceTrend

    # Create test provider
    provider = MarketDataProvider(
        name="test",
        display_name="Test Provider",
        base_url="test://",
        is_enabled=True,
        rate_limit_per_minute=60,
        config={}
    )
    db.add(provider)
    db.commit()

    # Create test price record with opening_price
    price_record = RealtimePriceHistory(
        symbol="CBA",
        price=Decimal('171.50'),  # Current price higher than opening
        opening_price=Decimal('170.00'),  # Opening price
        previous_close=Decimal('169.00'),
        provider_id=provider.id,
        source_timestamp=datetime.utcnow(),
        fetched_at=datetime.utcnow()
    )
    db.add(price_record)
    db.commit()

    # Test trend calculation
    trend_service = TrendCalculationService(db)
    trend_data = trend_service.calculate_trend("CBA")

    # Should show UP trend based on opening_price
    assert trend_data is not None
    assert trend_data.trend == PriceTrend.UP
    assert trend_data.current_price == Decimal('171.50')
    assert trend_data.opening_price == Decimal('170.00')  # Used opening_price, not previous_close
    assert trend_data.change == Decimal('1.50')  # 171.50 - 170.00
    assert trend_data.change_percent == Decimal('0.88')  # (1.50/170.00)*100 = 0.88%


def test_trend_calculation_fallback_to_previous_close(db: Session):
    """Test that trend calculation falls back to previous_close when opening_price is null."""
    from src.services.trend_calculation_service import TrendCalculationService, PriceTrend

    # Create test provider
    provider = MarketDataProvider(
        name="test",
        display_name="Test Provider",
        base_url="test://",
        is_enabled=True,
        rate_limit_per_minute=60,
        config={}
    )
    db.add(provider)
    db.commit()

    # Create test price record with null opening_price
    price_record = RealtimePriceHistory(
        symbol="TEST",
        price=Decimal('50.00'),
        opening_price=None,  # No opening price
        previous_close=Decimal('48.00'),  # Should fall back to this
        provider_id=provider.id,
        source_timestamp=datetime.utcnow(),
        fetched_at=datetime.utcnow()
    )
    db.add(price_record)
    db.commit()

    # Test trend calculation
    trend_service = TrendCalculationService(db)
    trend_data = trend_service.calculate_trend("TEST")

    # Should show UP trend based on previous_close fallback
    assert trend_data is not None
    assert trend_data.trend == PriceTrend.UP
    assert trend_data.current_price == Decimal('50.00')
    assert trend_data.opening_price == Decimal('48.00')  # Stored previous_close as reference
    assert trend_data.change == Decimal('2.00')  # 50.00 - 48.00
    assert trend_data.change_percent == Decimal('4.17')  # (2.00/48.00)*100 = 4.17%


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
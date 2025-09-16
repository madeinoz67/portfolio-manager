"""
TDD test for market data service stock table update bug.

The issue is that the market data scheduler updates realtime_price_history
but NOT the stocks table. Holdings page shows stale timestamps because
it reads from stock.last_price_update which is never updated.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models.stock import Stock
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.services.market_data_service import MarketDataService
from src.utils.datetime_utils import utc_now


class TestMarketDataStockUpdateBug:
    """Test that market data service updates both price history AND stocks table."""

    @pytest.fixture
    def market_data_service(self, db_session: Session):
        """Create market data service for testing."""
        return MarketDataService(db_session)

    @pytest.fixture
    def sample_stock(self, db_session: Session):
        """Create a sample stock with old timestamp."""
        old_time = utc_now() - timedelta(hours=4)

        stock = Stock(
            symbol="TEST",
            company_name="Test Company",
            exchange="ASX",
            current_price=Decimal("100.00"),
            last_price_update=old_time  # OLD timestamp
        )
        db_session.add(stock)
        db_session.commit()
        return stock

    def test_store_price_updates_both_history_and_stock_table(
        self, market_data_service, sample_stock, db_session
    ):
        """
        Test that store_price() updates BOTH realtime_price_history AND stocks table.

        BUG: Currently only updates realtime_price_history, leaving stock.last_price_update stale.
        This causes holdings to show old "Last Updated" times while market-data shows fresh times.
        """
        # Arrange: Get the stock before update
        old_timestamp = sample_stock.last_price_update

        # Mock price data (what would come from external API)
        price_data = {
            "symbol": "TEST",
            "price": Decimal("105.50"),
            "volume": 1000,
            "source_timestamp": utc_now(),
            "open_price": Decimal("100.00"),
            "high_price": Decimal("106.00"),
            "low_price": Decimal("99.50"),
            "previous_close": Decimal("100.00")
        }

        # Act: Store the price (this should update BOTH tables)
        # Get provider first
        provider = db_session.query(MarketDataProvider).first()
        if not provider:
            provider = MarketDataProvider(
                name="yahoo_finance",
                display_name="Yahoo Finance",
                api_key="",
                is_enabled=True
            )
            db_session.add(provider)
            db_session.commit()

        result = market_data_service._store_comprehensive_price_data(
            symbol="TEST",
            price_data=price_data,
            provider=provider,
            db_session=db_session
        )

        # Assert: Both tables should be updated

        # 1. Check realtime_price_history was created (this works currently)
        history_record = db_session.query(RealtimePriceHistory).filter_by(
            symbol="TEST"
        ).first()
        assert history_record is not None
        assert history_record.price == Decimal("105.50")
        assert history_record.fetched_at > old_timestamp

        # 2. Check stock table was ALSO updated (this is the bug - currently fails)
        db_session.refresh(sample_stock)
        assert sample_stock.current_price == Decimal("105.50")
        assert sample_stock.last_price_update > old_timestamp
        # This should be recent (within last minute)
        assert sample_stock.last_price_update > utc_now() - timedelta(minutes=1)

    def test_bulk_update_refreshes_all_stock_timestamps(
        self, market_data_service, db_session
    ):
        """
        Test that bulk price updates refresh stock.last_price_update for ALL symbols.

        This is critical for holdings to show current "Last Updated" times.
        """
        # Arrange: Create multiple stocks with old timestamps
        old_time = utc_now() - timedelta(hours=2)
        symbols = ["CBA", "BHP", "CSL"]

        for symbol in symbols:
            stock = Stock(
                symbol=symbol,
                company_name=f"{symbol} Company",
                exchange="ASX",
                current_price=Decimal("50.00"),
                last_price_update=old_time
            )
            db_session.add(stock)
        db_session.commit()

        # Mock bulk price data
        bulk_price_data = []
        for i, symbol in enumerate(symbols):
            bulk_price_data.append({
                "symbol": symbol,
                "price": Decimal(f"{60 + i}.00"),
                "volume": 1000 * (i + 1),
                "source_timestamp": utc_now(),
                "open_price": Decimal("50.00"),
                "high_price": Decimal("65.00"),
                "low_price": Decimal("49.00"),
                "previous_close": Decimal("50.00")
            })

        # Act: Store bulk prices
        for price_data in bulk_price_data:
            market_data_service.store_price(price_data)

        # Assert: ALL stock records should have updated timestamps
        for symbol in symbols:
            stock = db_session.query(Stock).filter_by(symbol=symbol).first()
            assert stock.last_price_update > old_time
            assert stock.last_price_update > utc_now() - timedelta(minutes=1)

    def test_stock_update_preserves_existing_data(
        self, market_data_service, sample_stock, db_session
    ):
        """
        Test that updating stock prices preserves other stock data.

        We only want to update current_price and last_price_update,
        not change company_name, exchange, etc.
        """
        # Arrange: Record original stock data
        original_company_name = sample_stock.company_name
        original_exchange = sample_stock.exchange
        original_symbol = sample_stock.symbol

        # Act: Update price
        price_data = {
            "symbol": "TEST",
            "price": Decimal("99.99"),
            "volume": 500,
            "source_timestamp": utc_now(),
            "open_price": Decimal("100.00"),
            "high_price": Decimal("101.00"),
            "low_price": Decimal("98.00"),
            "previous_close": Decimal("100.00")
        }
        market_data_service.store_price(price_data)

        # Assert: Only price and timestamp updated, other data preserved
        db_session.refresh(sample_stock)
        assert sample_stock.current_price == Decimal("99.99")
        assert sample_stock.last_price_update > utc_now() - timedelta(minutes=1)

        # Preserved data
        assert sample_stock.company_name == original_company_name
        assert sample_stock.exchange == original_exchange
        assert sample_stock.symbol == original_symbol

    def test_price_update_with_missing_stock_creates_new_record(
        self, market_data_service, db_session
    ):
        """
        Test that price updates for new symbols create stock records.

        This ensures holdings work for newly added symbols.
        """
        # Arrange: Ensure stock doesn't exist
        assert db_session.query(Stock).filter_by(symbol="NEWCO").first() is None

        # Act: Store price for new symbol
        price_data = {
            "symbol": "NEWCO",
            "price": Decimal("25.00"),
            "volume": 750,
            "source_timestamp": utc_now(),
            "open_price": Decimal("24.50"),
            "high_price": Decimal("25.50"),
            "low_price": Decimal("24.00"),
            "previous_close": Decimal("24.75"),
            "company_name": "New Company Ltd"  # Should be used if creating new stock
        }
        market_data_service.store_price(price_data)

        # Assert: New stock record created with current data
        new_stock = db_session.query(Stock).filter_by(symbol="NEWCO").first()
        assert new_stock is not None
        assert new_stock.current_price == Decimal("25.00")
        assert new_stock.last_price_update > utc_now() - timedelta(minutes=1)

        # Company name should be set if provided
        if "company_name" in price_data:
            assert new_stock.company_name == "New Company Ltd"
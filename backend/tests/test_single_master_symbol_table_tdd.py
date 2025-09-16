"""
TDD test suite for Single Master Symbol Table implementation.

This test defines the expected behavior for Option C (Hybrid):
- realtime_symbols table as single source of truth for current prices
- realtime_price_history maintained for time-series data
- Master table references latest history record
- All services read current prices from master table only

CRITICAL: This eliminates the dual-table synchronization complexity
that caused the holdings timestamp bug we just fixed.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.models.market_data_provider import MarketDataProvider
from src.services.market_data_service import MarketDataService
from src.utils.datetime_utils import utc_now


class TestSingleMasterSymbolTable:
    """Test suite for single master symbol table architecture."""

    @pytest.fixture
    def market_data_service(self, db_session: Session):
        """Create market data service for testing."""
        return MarketDataService(db_session)

    @pytest.fixture
    def test_provider(self, db_session: Session):
        """Create test provider."""
        provider = MarketDataProvider(
            name="test_provider",
            display_name="Test Provider",
            api_key="",
            is_enabled=True
        )
        db_session.add(provider)
        db_session.commit()
        return provider

    def test_realtime_symbols_table_exists(self, db_session: Session):
        """
        Test that realtime_symbols master table exists with correct schema.

        This table should be the SINGLE source of truth for current prices.
        """
        # SQLite-compatible schema check using PRAGMA table_info
        result = db_session.execute(text("PRAGMA table_info(realtime_symbols);"))
        table_info = result.fetchall()

        # Convert to dict for easier checking
        columns = {row[1]: {'type': row[2], 'not_null': bool(row[3])} for row in table_info}

        # Expected columns for master table
        expected_columns = {
            'symbol': {'not_null': True},      # Primary key
            'current_price': {'not_null': True},
            'company_name': {'not_null': False},
            'last_updated': {'not_null': True},
            'provider_id': {'not_null': True},
            'volume': {'not_null': False},
            'market_cap': {'not_null': False},
            'latest_history_id': {'not_null': False},  # References realtime_price_history
            'created_at': {'not_null': True},
            'updated_at': {'not_null': True}
        }

        # Ensure table exists and has expected columns
        assert len(columns) > 0, "realtime_symbols table does not exist or has no columns"

        for col_name, expected_props in expected_columns.items():
            assert col_name in columns, f"Column {col_name} missing from realtime_symbols"
            actual_props = columns[col_name]
            assert expected_props['not_null'] == actual_props['not_null'], f"Column {col_name} nullability mismatch"

    def test_single_write_to_master_table(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that price updates write to master table as single source of truth.

        This should eliminate the dual-write complexity that caused sync issues.
        """
        from src.models.realtime_symbol import RealtimeSymbol

        # Arrange: Price data for new symbol
        price_data = {
            "symbol": "AAPL",
            "price": Decimal("150.00"),
            "volume": 1000000,
            "source_timestamp": utc_now(),
            "company_name": "Apple Inc"
        }

        # Act: Store price (should write to master table)
        result = market_data_service.store_price_to_master(
            symbol="AAPL",
            price_data=price_data,
            provider=test_provider
        )

        # Assert: Master table updated
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol="AAPL").first()
        assert master_record is not None
        assert master_record.current_price == Decimal("150.00")
        assert master_record.company_name == "Apple Inc"
        assert master_record.provider_id == test_provider.id
        assert master_record.last_updated is not None

    def test_master_table_references_latest_history(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that master table maintains reference to latest history record.

        This provides the link between current state and historical data.
        """
        from src.models.realtime_symbol import RealtimeSymbol
        from src.models.realtime_price_history import RealtimePriceHistory

        # Arrange: Store price data
        price_data = {
            "symbol": "GOOGL",
            "price": Decimal("2500.00"),
            "volume": 500000,
            "source_timestamp": utc_now(),
            "company_name": "Alphabet Inc"
        }

        # Act: Store price
        market_data_service.store_price_to_master(
            symbol="GOOGL",
            price_data=price_data,
            provider=test_provider
        )

        # Assert: Master record references latest history
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol="GOOGL").first()
        history_record = db_session.query(RealtimePriceHistory).filter_by(
            id=master_record.latest_history_id
        ).first()

        assert history_record is not None
        assert history_record.symbol == "GOOGL"
        assert history_record.price == Decimal("2500.00")
        assert master_record.current_price == history_record.price

    def test_master_table_update_preserves_single_record_per_symbol(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that updating prices maintains single record per symbol in master.

        No duplicate symbols should exist in master table.
        """
        from src.models.realtime_symbol import RealtimeSymbol

        symbol = "MSFT"

        # Arrange: Initial price
        initial_price_data = {
            "symbol": symbol,
            "price": Decimal("300.00"),
            "volume": 750000,
            "source_timestamp": utc_now(),
            "company_name": "Microsoft Corp"
        }

        # Act: Store initial price
        market_data_service.store_price_to_master(
            symbol=symbol,
            price_data=initial_price_data,
            provider=test_provider
        )

        # Act: Update price
        updated_price_data = {
            "symbol": symbol,
            "price": Decimal("305.50"),
            "volume": 800000,
            "source_timestamp": utc_now(),
            "company_name": "Microsoft Corp"
        }

        market_data_service.store_price_to_master(
            symbol=symbol,
            price_data=updated_price_data,
            provider=test_provider
        )

        # Assert: Only one record exists for symbol
        master_records = db_session.query(RealtimeSymbol).filter_by(symbol=symbol).all()
        assert len(master_records) == 1

        # Assert: Record has updated price
        master_record = master_records[0]
        assert master_record.current_price == Decimal("305.50")
        assert master_record.volume == 800000

    def test_holdings_api_reads_from_master_table_only(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that holdings calculations use master table as single source.

        This ensures consistent pricing across all portfolio calculations.
        """
        from src.models.realtime_symbol import RealtimeSymbol
        from src.services.portfolio_service import PortfolioService

        # Arrange: Store price in master table
        price_data = {
            "symbol": "TSLA",
            "price": Decimal("800.00"),
            "volume": 2000000,
            "source_timestamp": utc_now(),
            "company_name": "Tesla Inc"
        }

        market_data_service.store_price_to_master(
            symbol="TSLA",
            price_data=price_data,
            provider=test_provider
        )

        # Act: Get price for holdings calculation
        portfolio_service = PortfolioService(db_session)
        current_price = portfolio_service.get_current_price("TSLA")

        # Assert: Price comes from master table
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol="TSLA").first()
        assert current_price == master_record.current_price
        assert current_price == Decimal("800.00")

    def test_market_data_api_reads_from_master_table_only(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that market data API uses master table as single source.

        This ensures API consistency with holdings data.
        """
        from src.models.realtime_symbol import RealtimeSymbol

        # Arrange: Store price in master table
        price_data = {
            "symbol": "NVDA",
            "price": Decimal("400.00"),
            "volume": 1500000,
            "source_timestamp": utc_now(),
            "company_name": "NVIDIA Corp"
        }

        market_data_service.store_price_to_master(
            symbol="NVDA",
            price_data=price_data,
            provider=test_provider
        )

        # Act: Get price via market data API method
        api_price_data = market_data_service.get_current_price_from_master("NVDA")

        # Assert: API returns master table data
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol="NVDA").first()
        assert api_price_data["price"] == master_record.current_price
        assert api_price_data["symbol"] == "NVDA"
        assert api_price_data["last_updated"] == master_record.last_updated

    def test_admin_dashboard_metrics_use_master_table(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that admin dashboard metrics read from master table.

        Critical: Must not break existing admin dashboard functionality.
        """
        from src.models.realtime_symbol import RealtimeSymbol
        from src.services.admin_dashboard_service import AdminDashboardService

        # Arrange: Store prices for multiple symbols
        symbols_data = [
            ("AMD", Decimal("100.00"), 500000),
            ("INTC", Decimal("50.00"), 750000),
            ("QCOM", Decimal("120.00"), 600000)
        ]

        for symbol, price, volume in symbols_data:
            price_data = {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "source_timestamp": utc_now(),
                "company_name": f"{symbol} Corp"
            }
            market_data_service.store_price_to_master(
                symbol=symbol,
                price_data=price_data,
                provider=test_provider
            )

        # Act: Get admin dashboard metrics
        admin_service = AdminDashboardService(db_session)
        metrics = admin_service.get_pricing_metrics()

        # Assert: Metrics calculated from master table
        assert metrics["total_symbols"] == 3
        assert metrics["avg_price"] == Decimal("90.00")  # (100 + 50 + 120) / 3
        assert all(symbol in metrics["symbol_prices"] for symbol, _, _ in symbols_data)

    def test_historical_data_preserved_in_price_history_table(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that historical data is maintained in realtime_price_history.

        Master table stores current state, history table stores time-series.
        """
        from src.models.realtime_symbol import RealtimeSymbol
        from src.models.realtime_price_history import RealtimePriceHistory

        symbol = "META"

        # Arrange: Store multiple price updates
        price_updates = [
            (Decimal("350.00"), utc_now() - timedelta(hours=2)),
            (Decimal("355.00"), utc_now() - timedelta(hours=1)),
            (Decimal("360.00"), utc_now())
        ]

        for price, timestamp in price_updates:
            price_data = {
                "symbol": symbol,
                "price": price,
                "volume": 1000000,
                "source_timestamp": timestamp,
                "company_name": "Meta Platforms"
            }
            market_data_service.store_price_to_master(
                symbol=symbol,
                price_data=price_data,
                provider=test_provider
            )

        # Assert: Master table has only latest price
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol=symbol).first()
        assert master_record.current_price == Decimal("360.00")

        # Assert: History table has all price updates
        history_records = db_session.query(RealtimePriceHistory).filter_by(
            symbol=symbol
        ).order_by(RealtimePriceHistory.source_timestamp).all()

        assert len(history_records) == 3
        assert [record.price for record in history_records] == [
            Decimal("350.00"), Decimal("355.00"), Decimal("360.00")
        ]

    def test_no_dual_write_complexity(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that price updates use single-write pattern.

        This should eliminate the synchronization bugs we just fixed.
        """
        from src.models.realtime_symbol import RealtimeSymbol
        from src.models.stock import Stock

        # Arrange: Price data
        price_data = {
            "symbol": "ORCL",
            "price": Decimal("75.00"),
            "volume": 800000,
            "source_timestamp": utc_now(),
            "company_name": "Oracle Corp"
        }

        # Act: Store price using new single-write method
        market_data_service.store_price_to_master(
            symbol="ORCL",
            price_data=price_data,
            provider=test_provider
        )

        # Assert: Master table updated
        master_record = db_session.query(RealtimeSymbol).filter_by(symbol="ORCL").first()
        assert master_record is not None
        assert master_record.current_price == Decimal("75.00")

        # Assert: Legacy stocks table should NOT be updated by new method
        # (This ensures clean separation during migration)
        stock_record = db_session.query(Stock).filter_by(symbol="ORCL").first()
        # Should be None or have different price (not updated by master method)
        if stock_record:
            assert stock_record.current_price != Decimal("75.00")

    def test_master_table_performance_optimized(self, db_session: Session):
        """
        Test that master table has proper indexes for performance.

        Critical for fast portfolio calculations and API responses.
        """
        # Test primary key index on symbol
        result = db_session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'realtime_symbols'
            AND indexname LIKE '%symbol%';
        """))

        indexes = {row[0]: row[1] for row in result.fetchall()}

        # Should have primary key index on symbol
        assert any('symbol' in idx_def for idx_def in indexes.values())

        # Test index on last_updated for freshness queries
        result = db_session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'realtime_symbols'
            AND indexname LIKE '%last_updated%';
        """))

        last_updated_indexes = [row[0] for row in result.fetchall()]
        assert len(last_updated_indexes) > 0, "Missing index on last_updated column"

    def test_foreign_key_integrity_maintained(
        self, market_data_service, test_provider, db_session
    ):
        """
        Test that foreign key relationships are properly maintained.

        Master table should reference valid providers and history records.
        """
        from src.models.realtime_symbol import RealtimeSymbol

        # Arrange: Store price data
        price_data = {
            "symbol": "SALESFORCE",
            "price": Decimal("200.00"),
            "volume": 400000,
            "source_timestamp": utc_now(),
            "company_name": "Salesforce Inc"
        }

        # Act: Store price
        market_data_service.store_price_to_master(
            symbol="SALESFORCE",
            price_data=price_data,
            provider=test_provider
        )

        # Assert: Foreign key references are valid
        master_record = db_session.query(RealtimeSymbol).filter_by(
            symbol="SALESFORCE"
        ).first()

        # Provider reference should be valid
        assert master_record.provider_id == test_provider.id
        assert master_record.provider is not None

        # History reference should be valid
        assert master_record.latest_history_id is not None
        assert master_record.latest_history is not None
        assert master_record.latest_history.symbol == "SALESFORCE"
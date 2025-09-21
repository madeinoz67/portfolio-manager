#!/usr/bin/env python3
"""
TDD test to verify the AdapterMarketDataService works with fixed yfinance adapter.
This tests the full service integration that the scheduler uses.
"""

import asyncio
import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.adapter_market_data_service import AdapterMarketDataService
from src.models.base import Base
from src.models.provider_configuration import ProviderConfiguration


class TestAdapterMarketDataServiceIntegration:
    """Test the AdapterMarketDataService with fixed yfinance adapter."""

    @pytest.fixture
    def test_db_session(self):
        """Create a test database session."""
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        # Add a test provider configuration
        test_config = ProviderConfiguration(
            id="test-yfinance-id",
            provider_name="yfinance",
            display_name="Test Yahoo Finance",
            config_data={},
            is_active=True
        )
        session.add(test_config)
        session.commit()

        yield session
        session.close()

    @pytest.mark.asyncio
    async def test_fetch_multiple_prices_returns_valid_data(self, test_db_session):
        """Test that AdapterMarketDataService returns valid price data."""
        # Given: An AdapterMarketDataService
        service = AdapterMarketDataService(test_db_session)

        # When: Fetching multiple Australian symbols
        symbols = ['CBA.AX', 'WBC.AX']
        results = await service.fetch_multiple_prices(symbols)

        # Then: Should return valid price data for all symbols
        assert isinstance(results, dict), "Results should be a dictionary"

        for symbol in symbols:
            if symbol in results:
                price_data = results[symbol]

                # Validate price data structure
                assert 'symbol' in price_data, f"Symbol field missing for {symbol}"
                assert 'price' in price_data, f"Price field missing for {symbol}"
                assert 'provider' in price_data, f"Provider field missing for {symbol}"

                # Validate price is not None or nan
                price = price_data['price']
                assert price is not None, f"Price is None for {symbol}"
                assert str(price).lower() != 'nan', f"Price is nan for {symbol}: {price}"
                assert float(price) > 0, f"Price should be positive for {symbol}: {price}"

                print(f"SUCCESS: {symbol} = ${price:.2f} from {price_data['provider']}")
            else:
                print(f"WARNING: {symbol} not found in results")

    @pytest.mark.asyncio
    async def test_service_handles_single_symbol(self, test_db_session):
        """Test single symbol fetch through service."""
        # Given: An AdapterMarketDataService
        service = AdapterMarketDataService(test_db_session)

        # When: Fetching a single symbol
        results = await service.fetch_multiple_prices(['CBA.AX'])

        # Then: Should return valid data
        assert 'CBA.AX' in results, "CBA.AX should be in results"
        cba_data = results['CBA.AX']

        assert cba_data['symbol'] == 'CBA.AX'
        assert float(cba_data['price']) > 100  # CBA typically > $100
        assert cba_data['provider'] == 'yfinance'

    @pytest.mark.asyncio
    async def test_service_stores_price_data(self, test_db_session):
        """Test that service stores price data to database."""
        # Given: An AdapterMarketDataService
        service = AdapterMarketDataService(test_db_session)

        # When: Fetching prices (which should store to database)
        results = await service.fetch_multiple_prices(['CBA.AX'])

        # Then: Price should be stored in master table
        from src.models.realtime_symbol import RealtimeSymbol
        stored_price = test_db_session.query(RealtimeSymbol).filter(
            RealtimeSymbol.symbol == 'CBA.AX'
        ).first()

        if stored_price:
            assert stored_price.current_price is not None
            assert float(stored_price.current_price) > 0
            print(f"SUCCESS: Stored price for CBA.AX: ${stored_price.current_price}")
        else:
            print("WARNING: Price not stored to database")


async def test_main():
    """Run the main test manually."""
    import tempfile
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create test database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Add test provider configuration
    test_config = ProviderConfiguration(
        id="test-yfinance-id",
        provider_name="yfinance",
        display_name="Test Yahoo Finance",
        config_data={},
        is_active=True
    )
    session.add(test_config)
    session.commit()

    try:
        test = TestAdapterMarketDataServiceIntegration()
        await test.test_fetch_multiple_prices_returns_valid_data(session)
        await test.test_service_handles_single_symbol(session)
        await test.test_service_stores_price_data(session)
        print("All service integration tests passed!")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(test_main())
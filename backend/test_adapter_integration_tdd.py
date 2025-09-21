#!/usr/bin/env python3
"""
TDD test to verify yfinance adapter fix works in full system integration.
Tests that adapter correctly fetches real market data without returning nan values.
"""

import asyncio
import sys
import os
import pytest
from decimal import Decimal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.adapters.yfinance_adapter import YFinanceAdapter
from services.adapters.base_adapter import AdapterResponse

class TestYFinanceAdapterIntegration:
    """Test the fixed yfinance adapter integration."""

    @pytest.mark.asyncio
    async def test_adapter_returns_valid_price_data(self):
        """Test that adapter returns valid price data without nan values."""
        # Given: A YFinanceAdapter instance
        config = {}
        adapter = YFinanceAdapter("test_provider", config)

        # When: Initializing and fetching Australian symbols
        await adapter.initialize()
        symbols = ['CBA.AX', 'WBC.AX']
        response = await adapter.fetch_prices(symbols)

        # Then: Response should be successful
        assert response.success, f"Adapter failed: {response.error}"
        assert response.data is not None, "Response data should not be None"

        # And: All symbols should have valid price data
        for symbol in symbols:
            assert symbol in response.data, f"Symbol {symbol} not in response"
            symbol_data = response.data[symbol]
            assert symbol_data is not None, f"Symbol {symbol} data is None"

            # Price should be a valid number, not nan
            price = symbol_data.get('price')
            assert price is not None, f"Price for {symbol} is None"
            assert str(price).lower() != 'nan', f"Price for {symbol} is nan: {price}"
            assert float(price) > 0, f"Price for {symbol} should be positive: {price}"

    @pytest.mark.asyncio
    async def test_adapter_handles_single_symbol_fetch(self):
        """Test single symbol fetch works correctly."""
        # Given: A YFinanceAdapter instance
        config = {}
        adapter = YFinanceAdapter("test_provider", config)

        # When: Fetching a single symbol
        await adapter.initialize()
        response = await adapter.fetch_prices(['CBA.AX'])

        # Then: Response should contain valid data
        assert response.success, f"Single symbol fetch failed: {response.error}"
        assert 'CBA.AX' in response.data

        cba_data = response.data['CBA.AX']
        assert cba_data['symbol'] == 'CBA.AX'
        assert float(cba_data['price']) > 100  # CBA should be > $100
        assert 'company_name' in cba_data

    @pytest.mark.asyncio
    async def test_adapter_health_check_passes(self):
        """Test that adapter health check passes after fix."""
        # Given: A YFinanceAdapter instance
        config = {}
        adapter = YFinanceAdapter("test_provider", config)

        # When: Running health check
        response = await adapter.health_check()

        # Then: Health check should pass
        assert response.success, f"Health check failed: {response.error}"
        assert response.data['status'] == 'healthy'

    @pytest.mark.asyncio
    async def test_adapter_converts_symbols_correctly(self):
        """Test that adapter correctly converts symbols to yfinance format."""
        # Given: A YFinanceAdapter instance
        config = {}
        adapter = YFinanceAdapter("test_provider", config)

        # When: Converting symbols
        asx_symbol = adapter._convert_symbol_for_yfinance('CBA')
        us_symbol = adapter._convert_symbol_for_yfinance('AAPL')
        already_converted = adapter._convert_symbol_for_yfinance('CBA.AX')

        # Then: Conversions should be correct
        assert asx_symbol == 'CBA.AX', f"ASX symbol conversion wrong: {asx_symbol}"
        assert us_symbol == 'AAPL', f"US symbol should not change: {us_symbol}"
        assert already_converted == 'CBA.AX', f"Already converted symbol changed: {already_converted}"

async def test_main():
    """Run the main test manually."""
    test = TestYFinanceAdapterIntegration()
    await test.test_adapter_returns_valid_price_data()
    await test.test_adapter_handles_single_symbol_fetch()
    await test.test_adapter_health_check_passes()
    await test.test_adapter_converts_symbols_correctly()
    print("All adapter integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_main())
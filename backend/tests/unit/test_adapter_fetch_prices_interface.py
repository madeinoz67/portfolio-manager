"""
TDD test for new fetch_prices interface design.
Tests that adapters can handle both single symbols and lists with a unified interface.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List, Union

from src.services.adapters.base_adapter import (
    MarketDataAdapter,
    AdapterResponse,
    ProviderCapabilities,
    CostInformation,
)


class TestFetchPricesInterface:
    """Test the new unified fetch_prices interface."""

    class NewInterfaceAdapter(MarketDataAdapter):
        """Concrete adapter implementing the new fetch_prices interface."""

        def __init__(self, config: Dict[str, Any]):
            super().__init__("test_unified_provider", config)
            self._should_fail = False
            self._use_bulk_api = True  # Simulate provider that prefers bulk

        @property
        def capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                supports_real_time=True,
                supports_historical=True,
                supports_bulk_quotes=True,
                max_symbols_per_request=100,
                rate_limit_per_minute=60
            )

        @property
        def cost_info(self) -> CostInformation:
            return CostInformation(
                cost_per_call=Decimal("0.001"),
                cost_model="per_call",
                monthly_quota=10000
            )

        async def initialize(self) -> bool:
            return True

        async def health_check(self) -> AdapterResponse:
            return AdapterResponse.success_response(
                data={"status": "healthy"},
                response_time_ms=10.0
            )

        async def fetch_prices(self, symbols: Union[str, List[str]]) -> AdapterResponse:
            """
            New unified interface that handles both single symbols and lists.
            Adapter internally decides whether to use single or bulk API calls.
            """
            if self._should_fail:
                return AdapterResponse.error_response("API error", "TEST_ERROR")

            # Normalize input to list for processing
            symbol_list = [symbols] if isinstance(symbols, str) else symbols

            # Simulate adapter making optimal API call decision
            if len(symbol_list) == 1 and not self._use_bulk_api:
                # Use single API call for one symbol
                result_data = self._mock_single_price_call(symbol_list[0])
            else:
                # Use bulk API call (provider preference or multiple symbols)
                result_data = self._mock_bulk_price_call(symbol_list)

            # Return results in same format regardless of input type
            if isinstance(symbols, str):
                # Single symbol input -> return single result
                return AdapterResponse.success_response(
                    data=result_data[symbols],
                    response_time_ms=150.0
                )
            else:
                # List input -> return dict of results
                return AdapterResponse.success_response(
                    data=result_data,
                    response_time_ms=200.0
                )

        def _mock_single_price_call(self, symbol: str) -> Dict[str, Any]:
            """Simulate single symbol API call."""
            return {
                symbol: {
                    "symbol": symbol,
                    "price": Decimal("150.25"),
                    "volume": 1000000,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "single_api"
                }
            }

        def _mock_bulk_price_call(self, symbols: List[str]) -> Dict[str, Any]:
            """Simulate bulk symbols API call."""
            results = {}
            for symbol in symbols:
                results[symbol] = {
                    "symbol": symbol,
                    "price": Decimal("150.25"),
                    "volume": 1000000,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "bulk_api"
                }
            return results

        # Legacy methods should not exist in new interface
        async def get_current_price(self, symbol: str) -> AdapterResponse:
            raise NotImplementedError("Use fetch_prices instead")

        async def get_multiple_prices(self, symbols: List[str]) -> AdapterResponse:
            raise NotImplementedError("Use fetch_prices instead")

    @pytest.mark.asyncio
    async def test_fetch_prices_single_symbol_string(self):
        """Test fetch_prices with single symbol as string."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        response = await adapter.fetch_prices("AAPL")

        assert response.success is True
        assert response.data["symbol"] == "AAPL"
        assert response.data["price"] == Decimal("150.25")
        assert "timestamp" in response.data

    @pytest.mark.asyncio
    async def test_fetch_prices_single_symbol_list(self):
        """Test fetch_prices with single symbol as list."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        response = await adapter.fetch_prices(["AAPL"])

        assert response.success is True
        assert "AAPL" in response.data
        assert response.data["AAPL"]["symbol"] == "AAPL"
        assert response.data["AAPL"]["price"] == Decimal("150.25")

    @pytest.mark.asyncio
    async def test_fetch_prices_multiple_symbols(self):
        """Test fetch_prices with multiple symbols."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})
        symbols = ["AAPL", "MSFT", "GOOGL"]

        response = await adapter.fetch_prices(symbols)

        assert response.success is True
        assert len(response.data) == 3
        for symbol in symbols:
            assert symbol in response.data
            assert response.data[symbol]["symbol"] == symbol
            assert response.data[symbol]["price"] == Decimal("150.25")

    @pytest.mark.asyncio
    async def test_fetch_prices_adapter_optimization_choice(self):
        """Test that adapter can choose optimal API strategy internally."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        # Force adapter to prefer bulk API even for single symbols
        adapter._use_bulk_api = True

        response = await adapter.fetch_prices("AAPL")

        assert response.success is True
        assert response.data["source"] == "bulk_api"  # Adapter chose bulk

    @pytest.mark.asyncio
    async def test_fetch_prices_single_api_preference(self):
        """Test adapter preferring single API for individual symbols."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        # Configure adapter to prefer single API calls
        adapter._use_bulk_api = False

        response = await adapter.fetch_prices("AAPL")

        assert response.success is True
        assert response.data["source"] == "single_api"  # Adapter chose single

    @pytest.mark.asyncio
    async def test_fetch_prices_error_handling(self):
        """Test fetch_prices error handling."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})
        adapter._should_fail = True

        response = await adapter.fetch_prices("AAPL")

        assert response.success is False
        assert response.error_message == "API error"
        assert response.error_code == "TEST_ERROR"

    @pytest.mark.asyncio
    async def test_fetch_prices_empty_list(self):
        """Test fetch_prices with empty symbol list."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        response = await adapter.fetch_prices([])

        assert response.success is True
        assert response.data == {}

    def test_legacy_methods_raise_not_implemented(self):
        """Test that legacy methods are deprecated and raise NotImplementedError."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        with pytest.raises(NotImplementedError, match="Use fetch_prices instead"):
            asyncio.run(adapter.get_current_price("AAPL"))

        with pytest.raises(NotImplementedError, match="Use fetch_prices instead"):
            asyncio.run(adapter.get_multiple_prices(["AAPL", "MSFT"]))

    @pytest.mark.asyncio
    async def test_fetch_prices_response_format_consistency(self):
        """Test that response format is consistent regardless of input type."""
        adapter = self.NewInterfaceAdapter({"api_key": "test"})

        # Single symbol as string
        single_response = await adapter.fetch_prices("AAPL")

        # Single symbol as list
        list_response = await adapter.fetch_prices(["AAPL"])

        # Multiple symbols
        multi_response = await adapter.fetch_prices(["AAPL", "MSFT"])

        # All should be successful AdapterResponse objects
        assert all(r.success for r in [single_response, list_response, multi_response])

        # Single string input returns single data object
        assert isinstance(single_response.data, dict)
        assert "symbol" in single_response.data

        # List input returns dict mapping
        assert isinstance(list_response.data, dict)
        assert "AAPL" in list_response.data

        assert isinstance(multi_response.data, dict)
        assert "AAPL" in multi_response.data
        assert "MSFT" in multi_response.data
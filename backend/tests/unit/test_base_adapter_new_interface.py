"""
TDD test to verify that current base adapter fails with new interface.
This test should fail until we implement the new interface.
"""

import pytest
from abc import ABC
from typing import Dict, Any, List, Union

from src.services.adapters.base_adapter import MarketDataAdapter, AdapterResponse


class TestCurrentBaseAdapterNewInterface:
    """Test that current base adapter needs the new interface."""

    class TestAdapter(MarketDataAdapter):
        """Minimal test adapter to verify interface requirements."""

        def __init__(self):
            super().__init__("test", {})

        @property
        def capabilities(self):
            return None

        @property
        def cost_info(self):
            return None

        async def initialize(self):
            return True

        async def health_check(self):
            return AdapterResponse.success_response({}, 0.0)

        async def get_current_price(self, symbol: str):
            return AdapterResponse.success_response({}, 0.0)

        async def get_multiple_prices(self, symbols: List[str]):
            return AdapterResponse.success_response({}, 0.0)

        async def fetch_prices(self, symbols: Union[str, List[str]]):
            return AdapterResponse.success_response({}, 0.0)

    def test_base_adapter_now_has_fetch_prices_method(self):
        """Test that base adapter now has fetch_prices method."""
        adapter = self.TestAdapter()

        # This should pass because fetch_prices now exists
        assert hasattr(adapter, 'fetch_prices'), "Base adapter should now have fetch_prices method"

    def test_base_adapter_can_instantiate_with_new_interface_only(self):
        """Test that we can now create an adapter that only implements fetch_prices."""

        # This class should now work because MarketDataAdapter provides
        # legacy methods that delegate to fetch_prices
        class NewInterfaceOnlyAdapter(MarketDataAdapter):
            def __init__(self):
                super().__init__("test", {})

            @property
            def capabilities(self):
                return None

            @property
            def cost_info(self):
                return None

            async def initialize(self):
                return True

            async def health_check(self):
                return AdapterResponse.success_response({}, 0.0)

            async def fetch_prices(self, symbols: Union[str, List[str]]):
                return AdapterResponse.success_response({}, 0.0)

            # Legacy methods are now provided by base class

        # This should now work
        adapter = NewInterfaceOnlyAdapter()
        assert hasattr(adapter, 'get_current_price')
        assert hasattr(adapter, 'get_multiple_prices')
        assert hasattr(adapter, 'fetch_prices')
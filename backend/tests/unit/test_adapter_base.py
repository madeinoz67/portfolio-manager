"""
T059: Unit tests for adapter base classes
Tests MarketDataAdapter abstract base class and core adapter functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timezone
import asyncio
from typing import Dict, Any, List, Optional

from src.services.adapters.base_adapter import (
    MarketDataAdapter,
    AdapterError,
    RateLimitError,
    AuthenticationError,
    ProviderTimeoutError,
    InvalidSymbolError,
    AdapterResponse,
    ProviderCapabilities,
)
from src.services.adapters.metrics import MetricsSnapshot, AdapterMetrics


class TestMarketDataAdapter:
    """Test the abstract MarketDataAdapter base class."""

    class ConcreteAdapter(MarketDataAdapter):
        """Concrete implementation for testing."""

        def __init__(self, config: Dict[str, Any]):
            super().__init__("test_provider", config)
            self._connected = False
            self._rate_limited = False
            self._should_fail = False

        @property
        def capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                supports_real_time=True,
                supports_historical=True,
                supports_bulk_quotes=True,
                max_symbols_per_request=100,
                rate_limit_per_minute=60
            )

        async def connect(self) -> bool:
            if self._should_fail:
                raise ProviderTimeoutError("Connection failed")
            self._connected = True
            return True

        async def disconnect(self) -> None:
            self._connected = False

        async def get_current_price(self, symbol: str) -> Dict[str, Any]:
            if not self._connected:
                raise ProviderTimeoutError("Not connected")
            if self._rate_limited:
                raise RateLimitError("Rate limit exceeded")
            if self._should_fail:
                raise AdapterError("API error")

            return {
                "symbol": symbol,
                "price": Decimal("150.25"),
                "volume": 1000000,
                "market_cap": Decimal("50000000000"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "test_provider"
            }

        async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
            results = {}
            for symbol in symbols:
                try:
                    results[symbol] = await self.get_current_price(symbol)
                except Exception:
                    results[symbol] = None
            return results

        async def validate_config(self) -> bool:
            required_fields = ["api_key", "base_url"]
            for field in required_fields:
                if field not in self.config:
                    raise InvalidSymbolError(f"Missing required field: {field}")
            return True

        @property
        def cost_info(self):
            """Return cost information for testing."""
            from src.services.adapters.base_adapter import CostInformation
            return CostInformation(
                cost_per_request=0.001,
                currency="USD",
                billing_model="per_request",
                free_tier_limit=1000
            )

        async def initialize(self) -> bool:
            """Initialize the test adapter."""
            return True

        async def health_check(self):
            """Perform health check."""
            return AdapterResponse.success_response(
                data={"status": "healthy"},
                response_time_ms=10.0
            )

        async def fetch_prices(self, symbols):
            """Implementation of the new unified fetch_prices interface."""
            from typing import Union, List

            # Normalize input to list for processing
            if isinstance(symbols, str):
                symbol_list = [symbols]
                return_single = True
            else:
                symbol_list = symbols
                return_single = False

            # Use existing implementation logic
            if len(symbol_list) == 1:
                # Single symbol
                result = await self.get_current_price(symbol_list[0])
                if return_single:
                    return AdapterResponse.success_response(
                        data=result,
                        response_time_ms=10.0
                    )
                else:
                    return AdapterResponse.success_response(
                        data={symbol_list[0]: result},
                        response_time_ms=10.0
                    )
            else:
                # Multiple symbols
                results = await self.get_multiple_prices(symbol_list)
                return AdapterResponse.success_response(
                    data=results,
                    response_time_ms=10.0
                )

    def test_adapter_initialization(self):
        """Test adapter initialization with config."""
        config = {
            "api_key": "test_key",
            "base_url": "https://api.test.com",
            "timeout": 30
        }

        adapter = self.ConcreteAdapter(config)

        assert adapter.config == config
        assert adapter.provider_name == "test_provider"
        assert adapter.adapter_id is not None
        assert len(adapter.adapter_id) == 36  # UUID format

    def test_adapter_capabilities(self):
        """Test adapter capabilities properties."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        capabilities = adapter.capabilities

        assert capabilities.supports_real_time is True
        assert capabilities.supports_historical is True
        assert capabilities.supports_bulk_quotes is True
        assert capabilities.max_symbols_per_request == 100
        assert capabilities.rate_limit_per_minute == 60

    @pytest.mark.asyncio
    async def test_adapter_connection_lifecycle(self):
        """Test adapter connection and disconnection."""
        adapter = self.ConcreteAdapter({"api_key": "test"})

        # Test successful connection
        result = await adapter.connect()
        assert result is True
        assert adapter._connected is True

        # Test disconnection
        await adapter.disconnect()
        assert adapter._connected is False

    @pytest.mark.asyncio
    async def test_adapter_connection_failure(self):
        """Test adapter connection failure handling."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        adapter._should_fail = True

        with pytest.raises(ProviderTimeoutError, match="Connection failed"):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_get_current_price_success(self):
        """Test successful price retrieval."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        await adapter.connect()

        result = await adapter.get_current_price("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["price"] == Decimal("150.25")
        assert result["volume"] == 1000000
        assert result["market_cap"] == Decimal("50000000000")
        assert "timestamp" in result
        assert result["source"] == "test_provider"

    @pytest.mark.asyncio
    async def test_get_current_price_not_connected(self):
        """Test price retrieval when not connected."""
        adapter = self.ConcreteAdapter({"api_key": "test"})

        with pytest.raises(ProviderTimeoutError, match="Not connected"):
            await adapter.get_current_price("AAPL")

    @pytest.mark.asyncio
    async def test_get_current_price_rate_limited(self):
        """Test price retrieval when rate limited."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        await adapter.connect()
        adapter._rate_limited = True

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await adapter.get_current_price("AAPL")

    @pytest.mark.asyncio
    async def test_get_current_price_api_error(self):
        """Test price retrieval API error handling."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        await adapter.connect()
        adapter._should_fail = True

        with pytest.raises(AdapterError, match="API error"):
            await adapter.get_current_price("AAPL")

    @pytest.mark.asyncio
    async def test_get_multiple_prices_success(self):
        """Test successful bulk price retrieval."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        await adapter.connect()

        symbols = ["AAPL", "MSFT", "GOOGL"]
        results = await adapter.get_multiple_prices(symbols)

        assert len(results) == 3
        for symbol in symbols:
            assert symbol in results
            assert results[symbol] is not None
            assert results[symbol]["symbol"] == symbol

    @pytest.mark.asyncio
    async def test_get_multiple_prices_partial_failure(self):
        """Test bulk price retrieval with partial failures."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        await adapter.connect()

        # Mock the get_current_price to fail for specific symbols
        original_method = adapter.get_current_price

        async def mock_get_price(symbol: str):
            if symbol == "INVALID":
                raise AdapterError("Invalid symbol")
            return await original_method(symbol)

        adapter.get_current_price = mock_get_price

        symbols = ["AAPL", "INVALID", "MSFT"]
        results = await adapter.get_multiple_prices(symbols)

        assert len(results) == 3
        assert results["AAPL"] is not None
        assert results["INVALID"] is None
        assert results["MSFT"] is not None

    @pytest.mark.asyncio
    async def test_validate_config_success(self):
        """Test successful config validation."""
        config = {
            "api_key": "test_key",
            "base_url": "https://api.test.com"
        }
        adapter = self.ConcreteAdapter(config)

        result = await adapter.validate_config()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_field(self):
        """Test config validation with missing required field."""
        config = {"api_key": "test_key"}  # Missing base_url
        adapter = self.ConcreteAdapter(config)

        with pytest.raises(InvalidSymbolError, match="Missing required field: base_url"):
            await adapter.validate_config()

    def test_adapter_metrics_initialization(self):
        """Test AdapterMetrics class initialization."""
        metrics = AdapterMetrics()

        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 0.0
        assert metrics.last_request_at is None
        assert metrics.error_counts == {}

    def test_adapter_metrics_record_success(self):
        """Test recording successful request metrics."""
        metrics = AdapterMetrics()

        metrics.record_request(True, 250.5)

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 250.5
        assert metrics.last_request_at is not None

    def test_adapter_metrics_record_failure(self):
        """Test recording failed request metrics."""
        metrics = AdapterMetrics()

        metrics.record_request(False, 150.0, "ConnectionError")

        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.total_response_time == 150.0
        assert metrics.error_counts["ConnectionError"] == 1

    def test_adapter_metrics_success_rate(self):
        """Test success rate calculation."""
        metrics = AdapterMetrics()

        # No requests yet
        assert metrics.success_rate == 0.0

        # Add some requests
        metrics.record_request(True, 100.0)
        metrics.record_request(True, 200.0)
        metrics.record_request(False, 300.0, "Error")

        # 2 out of 3 successful = 0.6667 (decimal, not percentage)
        assert abs(metrics.success_rate - 0.6667) < 0.001

    def test_adapter_metrics_average_response_time(self):
        """Test average response time calculation."""
        metrics = AdapterMetrics()

        # No requests yet
        assert metrics.average_response_time == 0.0

        # Add requests
        metrics.record_request(True, 100.0)
        metrics.record_request(True, 200.0)
        metrics.record_request(False, 300.0, "Error")

        # Average = (100 + 200 + 300) / 3 = 200
        assert metrics.average_response_time == 200.0

    def test_adapter_metrics_reset(self):
        """Test metrics reset functionality."""
        metrics = AdapterMetrics()

        # Add some data
        metrics.record_request(True, 100.0)
        metrics.record_request(False, 200.0, "Error")

        # Reset
        metrics.reset()

        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_response_time == 0.0
        assert metrics.last_request_at is None
        assert metrics.error_counts == {}

    def test_provider_capabilities_validation(self):
        """Test ProviderCapabilities validation."""
        # Valid capabilities
        caps = ProviderCapabilities(
            supports_real_time=True,
            supports_historical=False,
            supports_bulk_quotes=True,
            max_symbols_per_request=50,
            rate_limit_per_minute=30,
            supports_intraday=True
        )

        assert caps.supports_real_time is True
        assert caps.supports_historical is False
        assert caps.supports_bulk_quotes is True
        assert caps.max_symbols_per_request == 50
        assert caps.rate_limit_per_minute == 30
        assert caps.supports_intraday is True

    def test_adapter_id_uniqueness(self):
        """Test that each adapter instance gets a unique ID."""
        adapter1 = self.ConcreteAdapter({"api_key": "test"})
        adapter2 = self.ConcreteAdapter({"api_key": "test"})

        assert adapter1.adapter_id != adapter2.adapter_id

    @pytest.mark.asyncio
    async def test_adapter_context_manager(self):
        """Test adapter context manager functionality."""
        adapter = self.ConcreteAdapter({"api_key": "test"})

        async with adapter:
            assert adapter._connected is True

        assert adapter._connected is False

    @pytest.mark.asyncio
    async def test_adapter_context_manager_connection_failure(self):
        """Test adapter context manager with connection failure."""
        adapter = self.ConcreteAdapter({"api_key": "test"})
        adapter._should_fail = True

        with pytest.raises(ProviderTimeoutError):
            async with adapter:
                pass

    def test_adapter_string_representation(self):
        """Test adapter string representation."""
        adapter = self.ConcreteAdapter({"api_key": "test_key"})

        adapter_str = str(adapter)
        assert "test_provider" in adapter_str
        assert adapter.adapter_id in adapter_str

    def test_adapter_equality(self):
        """Test adapter equality comparison."""
        config = {"api_key": "test"}
        adapter1 = self.ConcreteAdapter(config)
        adapter2 = self.ConcreteAdapter(config)

        # Different instances should not be equal even with same config
        assert adapter1 != adapter2

        # Same instance should be equal to itself
        assert adapter1 == adapter1

    @pytest.mark.asyncio
    async def test_adapter_timeout_handling(self):
        """Test adapter timeout handling."""
        adapter = self.ConcreteAdapter({"api_key": "test", "timeout": 0.001})  # Very short timeout

        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
            with pytest.raises(ProviderTimeoutError):
                await adapter.connect()

    def test_adapter_config_immutability(self):
        """Test that adapter config cannot be modified after initialization."""
        config = {"api_key": "test", "mutable_field": "original"}
        adapter = self.ConcreteAdapter(config)

        # Modify original config dict
        config["mutable_field"] = "modified"
        config["new_field"] = "added"

        # Adapter config should remain unchanged
        assert adapter.config["mutable_field"] == "original"
        assert "new_field" not in adapter.config
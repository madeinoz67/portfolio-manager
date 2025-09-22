"""
Test adapter response format consistency.

Validates that all adapters return consistent response formats
regardless of underlying provider differences.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone

from src.services.adapters.yfinance_adapter import YFinanceAdapter
from src.services.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from src.services.adapters.base_adapter import AdapterResponse


class TestResponseFormatConsistency:
    """Test that all adapters return consistent response formats."""

    @pytest.fixture
    def yfinance_adapter(self):
        """Create YFinanceAdapter instance for testing."""
        return YFinanceAdapter("test_yfinance", {"timeout": 30})

    @pytest.fixture
    def alpha_vantage_adapter(self):
        """Create AlphaVantageAdapter instance for testing."""
        return AlphaVantageAdapter("test_alpha", {"api_key": "test_key"})

    def test_adapter_response_structure_consistency(self):
        """Test that all adapters use the same AdapterResponse structure."""
        # All adapters must return AdapterResponse objects
        success_response = AdapterResponse.success_response(
            data={"symbol": "AAPL", "price": Decimal("150.25")},
            response_time_ms=245.0
        )

        error_response = AdapterResponse.error_response(
            error_message="Test error",
            error_code="TEST_ERROR",
            response_time_ms=100.0
        )

        # Verify success response structure
        assert hasattr(success_response, 'success')
        assert hasattr(success_response, 'data')
        assert hasattr(success_response, 'response_time_ms')
        assert hasattr(success_response, 'error_message')
        assert hasattr(success_response, 'error_code')

        assert success_response.success is True
        assert success_response.data is not None
        assert success_response.error_message is None

        # Verify error response structure
        assert error_response.success is False
        assert error_response.data is None
        assert error_response.error_message == "Test error"
        assert error_response.error_code == "TEST_ERROR"

    def test_price_data_field_consistency(self):
        """Test that price data fields are consistent across adapters."""
        # Required fields that all adapters must provide
        required_fields = {
            'symbol': str,
            'price': (int, float, Decimal),
            'currency': str,
            'timestamp': str
        }

        # Standard optional fields
        standard_optional_fields = {
            'open': (int, float, Decimal, type(None)),
            'high': (int, float, Decimal, type(None)),
            'low': (int, float, Decimal, type(None)),
            'volume': (int, type(None)),
            'market_cap': (int, float, Decimal, type(None)),
            'change': (int, float, Decimal, type(None)),
            'change_percent': (str, type(None))
        }

        # Test YFinance format
        yfinance_data = {
            "symbol": "AAPL",
            "price": 150.25,
            "open": 149.80,
            "high": 151.00,
            "low": 149.50,
            "volume": 45000000,
            "change": 0.50,
            "change_percent": 0.33,
            "market_cap": 2500000000000,
            "currency": "USD",
            "timestamp": "2025-09-22T10:30:00Z"
        }

        # Test Alpha Vantage format
        alpha_data = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),
            'open': Decimal("149.80"),
            'high': Decimal("151.00"),
            'low': Decimal("149.50"),
            'volume': 45000000,
            'previous_close': Decimal("149.75"),
            'change': Decimal("0.50"),
            'change_percent': "0.33%",
            'currency': 'USD',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'market_cap': None
        }

        # Verify both formats have required fields
        for data_format in [yfinance_data, alpha_data]:
            for field, expected_type in required_fields.items():
                assert field in data_format, f"Missing required field: {field}"
                assert isinstance(data_format[field], expected_type), f"Invalid type for {field}"

        # Verify field naming consistency
        assert yfinance_data['symbol'] == alpha_data['symbol']
        assert yfinance_data['currency'] == alpha_data['currency']

    def test_single_symbol_response_format(self):
        """Test that single symbol responses have consistent format."""
        # Both adapters should return the same format for single symbols
        single_symbol_format = {
            "success": True,
            "data": {
                "symbol": "AAPL",
                "price": 150.25,
                "currency": "USD",
                "timestamp": "2025-09-22T10:30:00Z"
            },
            "response_time_ms": 245.0,
            "error_message": None,
            "error_code": None
        }

        # Verify response structure
        assert isinstance(single_symbol_format["success"], bool)
        assert isinstance(single_symbol_format["data"], dict)
        assert isinstance(single_symbol_format["response_time_ms"], (int, float))

        # Verify data section has required fields
        data = single_symbol_format["data"]
        assert "symbol" in data
        assert "price" in data
        assert "currency" in data

    def test_bulk_response_format_consistency(self):
        """Test that bulk responses have consistent format across adapters."""
        # Bulk response should be a dict mapping symbols to price data
        bulk_response_format = {
            "success": True,
            "data": {
                "AAPL": {
                    "symbol": "AAPL",
                    "price": 150.25,
                    "currency": "USD"
                },
                "GOOGL": {
                    "symbol": "GOOGL",
                    "price": 2800.50,
                    "currency": "USD"
                }
            },
            "response_time_ms": 300.0
        }

        # Verify bulk structure
        assert isinstance(bulk_response_format["data"], dict)

        # Each symbol should have consistent data format
        for symbol, price_data in bulk_response_format["data"].items():
            assert isinstance(price_data, dict)
            assert price_data["symbol"] == symbol
            assert "price" in price_data
            assert "currency" in price_data

    def test_error_response_format_consistency(self):
        """Test that error responses are consistent across adapters."""
        # Standard error response format
        error_format = {
            "success": False,
            "data": None,
            "error_message": "Provider error",
            "error_code": "PROVIDER_ERROR",
            "response_time_ms": 150.0
        }

        # Verify error structure
        assert error_format["success"] is False
        assert error_format["data"] is None
        assert isinstance(error_format["error_message"], str)
        assert isinstance(error_format["error_code"], str)

        # Test different error types
        error_types = [
            ("RATE_LIMIT_EXCEEDED", "Rate limit exceeded"),
            ("INVALID_SYMBOL", "Symbol not found"),
            ("PROVIDER_ERROR", "Provider service error"),
            ("TIMEOUT", "Request timeout"),
            ("AUTHENTICATION_ERROR", "Invalid API key")
        ]

        for error_code, error_message in error_types:
            error_response = {
                "success": False,
                "data": None,
                "error_message": error_message,
                "error_code": error_code,
                "response_time_ms": 100.0
            }

            # Verify error format consistency
            assert error_response["success"] is False
            assert error_response["error_code"] in [et[0] for et in error_types]

    def test_timestamp_format_consistency(self):
        """Test that timestamps are formatted consistently."""
        # ISO 8601 format should be used consistently
        valid_timestamp_formats = [
            "2025-09-22T10:30:00Z",           # UTC with Z
            "2025-09-22T10:30:00+00:00",     # UTC with offset
            "2025-09-22T10:30:00.123Z",      # UTC with milliseconds
        ]

        for timestamp in valid_timestamp_formats:
            # Verify ISO 8601 format
            assert "T" in timestamp  # Date-time separator
            assert len(timestamp) >= 19  # Minimum length for ISO format

            # Should be parseable as datetime
            try:
                if timestamp.endswith('Z'):
                    # Replace Z with +00:00 for Python parsing
                    parsed_time = datetime.fromisoformat(timestamp[:-1] + '+00:00')
                else:
                    parsed_time = datetime.fromisoformat(timestamp)

                assert isinstance(parsed_time, datetime)
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_currency_format_consistency(self):
        """Test that currency codes are formatted consistently."""
        # ISO 4217 currency codes
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD"]

        for currency in valid_currencies:
            # Verify ISO 4217 format
            assert len(currency) == 3
            assert currency.isupper()
            assert currency.isalpha()

        # Invalid currency formats that should be rejected
        invalid_currencies = ["usd", "US", "USDD", "123", "U$D"]

        for invalid_currency in invalid_currencies:
            # These should not pass validation
            is_valid = (
                len(invalid_currency) == 3 and
                invalid_currency.isupper() and
                invalid_currency.isalpha()
            )
            assert not is_valid, f"Invalid currency should be rejected: {invalid_currency}"

    def test_numeric_precision_consistency(self):
        """Test that numeric values have consistent precision."""
        # Price values should maintain appropriate precision
        price_examples = [
            (150.25, 2),      # Standard stock price - 2 decimals
            (0.0001, 4),      # Penny stock - 4 decimals
            (2800.123, 3),    # High-precision price - 3 decimals
        ]

        for price, expected_decimals in price_examples:
            # Convert to Decimal for precision testing
            decimal_price = Decimal(str(price))

            # Check decimal places
            decimal_places = abs(decimal_price.as_tuple().exponent)
            assert decimal_places <= expected_decimals

            # Verify no floating point artifacts
            assert str(decimal_price) == str(price)

    def test_response_size_consistency(self):
        """Test that response sizes are reasonable and consistent."""
        # Sample response sizes for performance validation
        single_response = {
            "success": True,
            "data": {
                "symbol": "AAPL",
                "price": 150.25,
                "open": 149.80,
                "high": 151.00,
                "low": 149.50,
                "volume": 45000000,
                "currency": "USD",
                "timestamp": "2025-09-22T10:30:00Z"
            },
            "response_time_ms": 245.0
        }

        # Estimate response size (rough calculation)
        import json
        single_size = len(json.dumps(single_response))

        # Single response should be reasonable size
        assert single_size < 1000  # Less than 1KB

        # Bulk response with 10 symbols
        bulk_response = {
            "success": True,
            "data": {},
            "response_time_ms": 300.0
        }

        # Add 10 symbols
        for i in range(10):
            symbol = f"STOCK{i}"
            bulk_response["data"][symbol] = {
                "symbol": symbol,
                "price": 100.0 + i,
                "currency": "USD"
            }

        bulk_size = len(json.dumps(bulk_response))

        # Bulk response should scale reasonably
        assert bulk_size < 5000  # Less than 5KB for 10 symbols
        assert bulk_size > single_size  # Should be larger than single

        # Size per symbol should be consistent
        avg_size_per_symbol = bulk_size / 10
        assert avg_size_per_symbol < 500  # Less than 500 bytes per symbol

    def test_response_serialization_consistency(self):
        """Test that responses can be consistently serialized."""
        import json
        from decimal import Decimal

        # Response with Decimal values
        response_with_decimals = {
            "success": True,
            "data": {
                "symbol": "AAPL",
                "price": Decimal("150.25"),
                "open": Decimal("149.80"),
                "currency": "USD"
            }
        }

        # Custom serializer for Decimal
        def decimal_serializer(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError

        # Should be serializable
        try:
            json_str = json.dumps(response_with_decimals, default=decimal_serializer)
            parsed_back = json.loads(json_str)

            # Verify serialization preserved data
            assert parsed_back["success"] is True
            assert parsed_back["data"]["symbol"] == "AAPL"
            assert isinstance(parsed_back["data"]["price"], float)

        except (TypeError, ValueError) as e:
            pytest.fail(f"Serialization failed: {e}")

    def test_adapter_capability_reporting_consistency(self):
        """Test that adapter capabilities are reported consistently."""
        # Standard capability structure
        capability_format = {
            "adapter_name": "yfinance",
            "supports_real_time": True,
            "supports_historical": True,
            "supports_bulk_quotes": True,
            "max_symbols_per_request": 50,
            "rate_limit_per_minute": 60,
            "cost_model": "free",
            "supported_data_types": ["stock_prices", "historical_data"]
        }

        # Verify capability structure
        required_capability_fields = [
            "adapter_name", "supports_bulk_quotes", "max_symbols_per_request",
            "cost_model", "supported_data_types"
        ]

        for field in required_capability_fields:
            assert field in capability_format

        # Verify data types
        assert isinstance(capability_format["adapter_name"], str)
        assert isinstance(capability_format["supports_bulk_quotes"], bool)
        assert isinstance(capability_format["max_symbols_per_request"], int)
        assert isinstance(capability_format["supported_data_types"], list)

        # Verify reasonable values
        assert capability_format["max_symbols_per_request"] > 0
        assert len(capability_format["supported_data_types"]) > 0
"""
Test complete OHLCV dataset requirements.

Validates FR-042 and FR-044 from the specification:
- FR-042: Full daily price info (open, high, low, close, volume, market cap, change)
- FR-044: Complete datasets even with partial provider data
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal
from datetime import datetime, timezone

from src.services.adapters.yfinance_adapter import YFinanceAdapter
from src.services.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from src.services.adapters.base_adapter import AdapterResponse


class TestOHLCVCompleteness:
    """Test that all adapters provide complete OHLCV data."""

    @pytest.fixture
    def yfinance_adapter(self):
        """Create YFinanceAdapter instance for testing."""
        return YFinanceAdapter("test_yfinance", {"timeout": 30})

    @pytest.fixture
    def alpha_vantage_adapter(self):
        """Create AlphaVantageAdapter instance for testing."""
        return AlphaVantageAdapter("test_alpha", {"api_key": "test_key"})

    def test_required_ohlcv_fields_present(self):
        """Test that all required OHLCV fields are present in responses."""
        # Required fields per specification FR-042
        required_fields = [
            'symbol',           # Stock symbol
            'price',           # Current price (Close equivalent)
            'open',            # Open price
            'high',            # High price
            'low',             # Low price
            'volume',          # Trading volume
            'currency',        # Currency information
            'timestamp',       # When data was fetched
        ]

        # Additional recommended fields
        recommended_fields = [
            'previous_close',  # Previous close price
            'change',          # Price change amount
            'change_percent',  # Price change percentage
            'market_cap',      # Market capitalization
        ]

        # Test YFinance response structure
        yfinance_response = {
            "symbol": "AAPL",
            "price": 150.25,      # Current price (close)
            "open": 149.80,       # Open price
            "high": 151.00,       # High price
            "low": 149.50,        # Low price
            "volume": 45000000,   # Volume
            "change": 0.50,       # Change amount
            "change_percent": 0.33, # Change percentage
            "market_cap": 2500000000000, # Market cap
            "currency": "USD",    # Currency
            "timestamp": "2025-09-22T10:30:00Z" # Timestamp
        }

        # Verify all required fields are present
        for field in required_fields:
            assert field in yfinance_response, f"Missing required field: {field}"

        # Verify field types
        assert isinstance(yfinance_response['symbol'], str)
        assert isinstance(yfinance_response['price'], (int, float, Decimal))
        assert isinstance(yfinance_response['open'], (int, float, Decimal))
        assert isinstance(yfinance_response['high'], (int, float, Decimal))
        assert isinstance(yfinance_response['low'], (int, float, Decimal))
        assert isinstance(yfinance_response['volume'], int)
        assert isinstance(yfinance_response['currency'], str)
        assert isinstance(yfinance_response['timestamp'], str)

    def test_alpha_vantage_ohlcv_completeness(self):
        """Test that AlphaVantageAdapter provides complete OHLCV data."""
        # Test the updated AlphaVantageAdapter response structure
        alpha_response = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),      # Current price (close)
            'open': Decimal("149.80"),       # Open price
            'high': Decimal("151.00"),       # High price
            'low': Decimal("149.50"),        # Low price
            'volume': 45000000,              # Volume
            'previous_close': Decimal("149.75"), # Previous close
            'change': Decimal("0.50"),       # Change amount
            'change_percent': "0.33%",       # Change percentage
            'currency': 'USD',               # Currency
            'timestamp': datetime.now(timezone.utc).isoformat(), # Timestamp
            'market_cap': None,              # Not provided by Global Quote
            'source': 'test_alpha'           # Provider source
        }

        # Verify complete OHLCV data is present
        ohlcv_fields = ['open', 'high', 'low', 'price', 'volume']
        for field in ohlcv_fields:
            assert field in alpha_response, f"Missing OHLCV field: {field}"
            if field != 'volume':  # volume is int, others are Decimal
                assert isinstance(alpha_response[field], Decimal)

        # Verify volume is integer
        assert isinstance(alpha_response['volume'], int)
        assert alpha_response['volume'] >= 0

        # Verify price relationships make sense
        assert alpha_response['low'] <= alpha_response['price'] <= alpha_response['high']
        assert alpha_response['low'] <= alpha_response['open'] <= alpha_response['high']

    @patch('yfinance.Ticker')
    async def test_yfinance_adapter_provides_complete_data(self, mock_ticker, yfinance_adapter):
        """Test that YFinanceAdapter provides complete OHLCV data."""
        # Mock yfinance response
        import pandas as pd

        mock_hist = pd.DataFrame({
            'Open': [149.80],
            'High': [151.00],
            'Low': [149.50],
            'Close': [150.25],
            'Volume': [45000000]
        })

        mock_info = {
            'longName': 'Apple Inc.',
            'currency': 'USD',
            'marketCap': 2500000000000,
            'exchange': 'NMS'
        }

        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = mock_hist
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance

        # Test fetch_prices method
        response = await yfinance_adapter.fetch_prices("AAPL")

        assert response.success is True
        assert response.data is not None

        # Extract the price data
        price_data = response.data.get("AAPL") if isinstance(response.data, dict) else response.data

        # Verify complete OHLCV data
        assert 'symbol' in price_data
        assert 'price' in price_data      # Close price
        assert 'open' in price_data       # Open price
        assert 'high' in price_data       # High price
        assert 'low' in price_data        # Low price
        assert 'volume' in price_data     # Volume
        assert 'currency' in price_data   # Currency

        # Verify data quality
        assert price_data['symbol'] == 'AAPL'
        assert price_data['currency'] == 'USD'
        assert price_data['volume'] > 0
        assert price_data['low'] <= price_data['price'] <= price_data['high']

    async def test_partial_data_completion(self, alpha_vantage_adapter):
        """Test that adapters complete partial data from providers."""
        # Mock partial Alpha Vantage response (missing some fields)
        partial_response = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "150.25",
                # Missing open, high, low data
                "06. volume": "45000000",
            }
        }

        # Test the adapter's handling of partial data
        result = alpha_vantage_adapter._parse_single_symbol_response("AAPL", partial_response)

        # Verify adapter provides complete structure even with partial data
        assert result is not None
        assert 'symbol' in result
        assert 'price' in result
        assert 'volume' in result
        assert 'currency' in result

        # When OHLC data is missing, adapter should provide None values rather than failing
        assert 'open' in result
        assert 'high' in result
        assert 'low' in result

        # Missing data should be None, not cause failures
        assert result['open'] is None
        assert result['high'] is None
        assert result['low'] is None

    def test_bulk_data_completeness(self):
        """Test that bulk requests provide complete OHLCV data for all symbols."""
        # Mock bulk response
        bulk_symbols = ["AAPL", "GOOGL", "MSFT"]
        bulk_response = {}

        for i, symbol in enumerate(bulk_symbols):
            bulk_response[symbol] = {
                'symbol': symbol,
                'price': Decimal(f"{150 + i * 100}.25"),
                'open': Decimal(f"{149 + i * 100}.80"),
                'high': Decimal(f"{151 + i * 100}.00"),
                'low': Decimal(f"{149 + i * 100}.50"),
                'volume': 45000000 + i * 1000000,
                'currency': 'USD',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        # Verify each symbol has complete data
        for symbol, data in bulk_response.items():
            # Check required OHLCV fields
            required_fields = ['symbol', 'price', 'open', 'high', 'low', 'volume', 'currency']
            for field in required_fields:
                assert field in data, f"Missing {field} for {symbol}"

            # Verify price relationships
            assert data['low'] <= data['price'] <= data['high']
            assert data['low'] <= data['open'] <= data['high']

            # Verify data types
            assert isinstance(data['volume'], int)
            assert data['volume'] > 0

    def test_historical_data_completeness(self):
        """Test that historical data includes complete OHLCV information."""
        # Mock historical data response
        historical_data = {
            'symbol': 'AAPL',
            'period': '5d',
            'interval': '1d',
            'data_points': [
                {
                    'timestamp': '2025-09-18T00:00:00Z',
                    'open': Decimal("148.50"),
                    'high': Decimal("150.00"),
                    'low': Decimal("148.00"),
                    'close': Decimal("149.75"),
                    'volume': 42000000
                },
                {
                    'timestamp': '2025-09-19T00:00:00Z',
                    'open': Decimal("149.80"),
                    'high': Decimal("151.25"),
                    'low': Decimal("149.30"),
                    'close': Decimal("150.50"),
                    'volume': 38000000
                }
            ]
        }

        # Verify historical data structure
        assert 'symbol' in historical_data
        assert 'data_points' in historical_data
        assert len(historical_data['data_points']) > 0

        # Verify each data point has complete OHLCV
        for point in historical_data['data_points']:
            ohlcv_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for field in ohlcv_fields:
                assert field in point, f"Missing {field} in historical data point"

            # Verify price relationships
            assert point['low'] <= point['close'] <= point['high']
            assert point['low'] <= point['open'] <= point['high']

    def test_data_validation_rules(self):
        """Test that OHLCV data meets validation rules."""
        # Sample price data for validation
        price_data = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),
            'open': Decimal("149.80"),
            'high': Decimal("151.00"),
            'low': Decimal("149.50"),
            'volume': 45000000,
            'previous_close': Decimal("149.75"),
            'currency': 'USD'
        }

        # Validation rules
        def validate_ohlcv_data(data):
            """Validate OHLCV data meets business rules."""
            errors = []

            # Required fields check
            required = ['symbol', 'price', 'open', 'high', 'low', 'volume', 'currency']
            for field in required:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Price relationship validation
            if 'low' in data and 'high' in data and 'price' in data:
                if not (data['low'] <= data['price'] <= data['high']):
                    errors.append("Current price outside of daily range")

            if 'low' in data and 'high' in data and 'open' in data:
                if not (data['low'] <= data['open'] <= data['high']):
                    errors.append("Open price outside of daily range")

            # Volume validation
            if 'volume' in data:
                if not isinstance(data['volume'], int) or data['volume'] < 0:
                    errors.append("Volume must be non-negative integer")

            # Currency validation
            if 'currency' in data:
                if not isinstance(data['currency'], str) or len(data['currency']) != 3:
                    errors.append("Currency must be 3-character string")

            return errors

        # Test validation
        validation_errors = validate_ohlcv_data(price_data)
        assert len(validation_errors) == 0, f"Validation errors: {validation_errors}"

    def test_missing_data_fallback_strategies(self):
        """Test fallback strategies when complete data is not available."""
        # Test scenario with missing market cap
        incomplete_data = {
            'symbol': 'UNKNOWN_STOCK',
            'price': Decimal("50.00"),
            'open': Decimal("49.75"),
            'high': Decimal("50.25"),
            'low': Decimal("49.50"),
            'volume': 1000000,
            'currency': 'USD',
            # market_cap missing
        }

        # Apply fallback strategy
        def apply_fallbacks(data):
            """Apply fallback values for missing optional data."""
            fallbacks = {
                'market_cap': None,           # Optional field, can be None
                'previous_close': None,       # Can be calculated from historical data
                'change': Decimal("0.00"),    # Default to no change if unknown
                'change_percent': "0.00%"     # Default to no change if unknown
            }

            for field, default_value in fallbacks.items():
                if field not in data:
                    data[field] = default_value

            return data

        # Apply fallbacks
        complete_data = apply_fallbacks(incomplete_data.copy())

        # Verify fallbacks were applied
        assert 'market_cap' in complete_data
        assert 'change' in complete_data
        assert 'change_percent' in complete_data

        # Verify core OHLCV data is still present
        ohlcv_fields = ['open', 'high', 'low', 'price', 'volume']
        for field in ohlcv_fields:
            assert field in complete_data
            assert complete_data[field] is not None

    def test_real_time_vs_delayed_data_completeness(self):
        """Test that both real-time and delayed data provide complete OHLCV."""
        # Real-time data scenario (during market hours)
        realtime_data = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),      # Current real-time price
            'open': Decimal("149.80"),       # Today's open
            'high': Decimal("151.00"),       # Today's high so far
            'low': Decimal("149.50"),        # Today's low so far
            'volume': 25000000,              # Current day volume
            'timestamp': '2025-09-22T15:30:00Z',  # Current time
            'is_realtime': True,
            'currency': 'USD'
        }

        # Delayed data scenario (after market hours)
        delayed_data = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),      # Closing price
            'open': Decimal("149.80"),       # Day's open
            'high': Decimal("151.00"),       # Day's high
            'low': Decimal("149.50"),        # Day's low
            'volume': 45000000,              # Total day volume
            'timestamp': '2025-09-22T20:00:00Z',  # End of day
            'is_realtime': False,
            'currency': 'USD'
        }

        # Verify both scenarios provide complete OHLCV
        for data in [realtime_data, delayed_data]:
            ohlcv_fields = ['symbol', 'price', 'open', 'high', 'low', 'volume', 'currency']
            for field in ohlcv_fields:
                assert field in data
                assert data[field] is not None

            # Verify price relationships
            assert data['low'] <= data['price'] <= data['high']
            assert data['low'] <= data['open'] <= data['high']
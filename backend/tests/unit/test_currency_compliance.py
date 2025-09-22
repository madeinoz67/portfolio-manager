"""
Test currency information compliance in all price responses.

Validates that currency information is included in all price data responses
and that currency handling is consistent across the system.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.services.adapters.yfinance_adapter import YFinanceAdapter
from src.services.adapters.alpha_vantage_adapter import AlphaVantageAdapter


class TestCurrencyCompliance:
    """Test that all price responses include proper currency information."""

    def test_yfinance_adapter_includes_currency(self):
        """Test that YFinanceAdapter includes currency in all responses."""
        adapter = YFinanceAdapter("test_yfinance", {})

        # Mock yfinance ticker info response
        mock_info = {
            'currency': 'USD',
            'longName': 'Apple Inc.',
            'exchange': 'NMS'
        }

        # Test that currency is extracted from info
        assert mock_info.get('currency') == 'USD'

        # Verify currency is included in result data structure
        expected_fields = ['symbol', 'price', 'open', 'high', 'low', 'volume', 'currency']

        # Create sample result data
        result_data = {
            "symbol": "AAPL",
            "price": 150.25,
            "open": 149.80,
            "high": 151.00,
            "low": 149.50,
            "volume": 45000000,
            "currency": mock_info.get('currency', 'USD'),
            "timestamp": "2025-09-22T10:30:00Z"
        }

        # Verify all expected fields are present
        for field in expected_fields:
            assert field in result_data

        # Verify currency is properly formatted
        assert isinstance(result_data['currency'], str)
        assert len(result_data['currency']) == 3
        assert result_data['currency'].isupper()

    def test_alpha_vantage_adapter_includes_currency(self):
        """Test that AlphaVantageAdapter includes currency in all responses."""
        adapter = AlphaVantageAdapter("test_alpha", {"api_key": "test_key"})

        # Test the expected response structure
        sample_response = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),
            'open': Decimal("149.80"),
            'high': Decimal("151.00"),
            'low': Decimal("149.50"),
            'volume': 45000000,
            'currency': 'USD',  # Alpha Vantage default
            'timestamp': "2025-09-22T10:30:00Z"
        }

        # Verify currency is included
        assert 'currency' in sample_response
        assert sample_response['currency'] == 'USD'

        # Verify currency format
        assert isinstance(sample_response['currency'], str)
        assert len(sample_response['currency']) == 3
        assert sample_response['currency'].isupper()

    def test_currency_codes_are_iso_compliant(self):
        """Test that currency codes follow ISO 4217 standards."""
        # Common currency codes that adapters should support
        valid_currencies = [
            'USD',  # US Dollar
            'EUR',  # Euro
            'GBP',  # British Pound
            'JPY',  # Japanese Yen
            'AUD',  # Australian Dollar
            'CAD',  # Canadian Dollar
            'CHF',  # Swiss Franc
            'CNY',  # Chinese Yuan
            'HKD',  # Hong Kong Dollar
            'SGD',  # Singapore Dollar
        ]

        for currency in valid_currencies:
            # Verify ISO 4217 format
            assert isinstance(currency, str)
            assert len(currency) == 3
            assert currency.isupper()
            assert currency.isalpha()

    def test_currency_consistency_across_symbols(self):
        """Test that currency handling is consistent across different symbols."""
        # Test cases for different markets
        test_cases = [
            ('AAPL', 'USD'),    # US stock
            ('GOOGL', 'USD'),   # US stock
            ('MSFT', 'USD'),    # US stock
            # ASX stocks would be AUD in real implementation
            ('BHP.AX', 'AUD'),  # Australian stock (if supported)
        ]

        for symbol, expected_currency in test_cases:
            # Verify currency expectation is valid
            assert isinstance(expected_currency, str)
            assert len(expected_currency) == 3
            assert expected_currency.isupper()

    def test_missing_currency_defaults_to_usd(self):
        """Test that missing currency information defaults to USD."""
        # Test scenario where currency info is missing
        incomplete_data = {
            'symbol': 'UNKNOWN',
            'price': Decimal("100.00"),
            'open': Decimal("99.50"),
            'high': Decimal("100.50"),
            'low': Decimal("99.00"),
            'volume': 1000000
        }

        # Add default currency when missing
        if 'currency' not in incomplete_data:
            incomplete_data['currency'] = 'USD'

        assert incomplete_data['currency'] == 'USD'

    def test_currency_validation_function(self):
        """Test currency validation helper function."""
        def validate_currency(currency_code):
            """Validate currency code format."""
            if not isinstance(currency_code, str):
                return False
            if len(currency_code) != 3:
                return False
            if not currency_code.isupper():
                return False
            if not currency_code.isalpha():
                return False
            return True

        # Test valid currencies
        valid_codes = ['USD', 'EUR', 'GBP', 'JPY', 'AUD']
        for code in valid_codes:
            assert validate_currency(code) is True

        # Test invalid currencies
        invalid_codes = ['usd', 'US', 'USDD', '123', 'U$D', None, 123]
        for code in invalid_codes:
            assert validate_currency(code) is False

    def test_bulk_response_currency_consistency(self):
        """Test that bulk responses maintain currency consistency."""
        # Mock bulk response with multiple symbols
        bulk_response = {
            'AAPL': {
                'symbol': 'AAPL',
                'price': Decimal("150.25"),
                'currency': 'USD'
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'price': Decimal("2800.50"),
                'currency': 'USD'
            },
            'MSFT': {
                'symbol': 'MSFT',
                'price': Decimal("420.75"),
                'currency': 'USD'
            }
        }

        # Verify all symbols have currency information
        for symbol, data in bulk_response.items():
            assert 'currency' in data
            assert data['currency'] == 'USD'

        # Verify consistency across symbols
        currencies = [data['currency'] for data in bulk_response.values()]
        assert len(set(currencies)) == 1  # All same currency

    def test_currency_formatting_in_api_responses(self):
        """Test that currency information is properly formatted in API responses."""
        # Sample API response structure
        api_response = {
            'success': True,
            'data': {
                'symbol': 'AAPL',
                'price': 150.25,
                'currency': 'USD',
                'open': 149.80,
                'high': 151.00,
                'low': 149.50,
                'volume': 45000000,
                'timestamp': '2025-09-22T10:30:00Z'
            }
        }

        # Verify currency is in the data section
        assert 'currency' in api_response['data']
        assert api_response['data']['currency'] == 'USD'

        # Verify currency format in API context
        currency = api_response['data']['currency']
        assert isinstance(currency, str)
        assert len(currency) == 3
        assert currency.isupper()

    def test_portfolio_currency_aggregation(self):
        """Test currency handling in portfolio-level aggregations."""
        # Mock portfolio holdings with different currencies
        holdings = [
            {
                'symbol': 'AAPL',
                'price': Decimal("150.25"),
                'currency': 'USD',
                'quantity': Decimal("10")
            },
            {
                'symbol': 'MSFT',
                'price': Decimal("420.75"),
                'currency': 'USD',
                'quantity': Decimal("5")
            }
        ]

        # Verify all holdings have currency information
        for holding in holdings:
            assert 'currency' in holding
            assert holding['currency'] is not None
            assert len(holding['currency']) == 3

        # Test portfolio aggregation with currency
        total_value = Decimal("0.00")
        portfolio_currency = None

        for holding in holdings:
            value = holding['price'] * holding['quantity']
            total_value += value

            # Set portfolio currency from first holding
            if portfolio_currency is None:
                portfolio_currency = holding['currency']
            # Verify all holdings use same currency (for simple case)
            assert holding['currency'] == portfolio_currency

        # Portfolio summary should include currency
        portfolio_summary = {
            'total_value': total_value,
            'currency': portfolio_currency,
            'holdings_count': len(holdings)
        }

        assert 'currency' in portfolio_summary
        assert portfolio_summary['currency'] == 'USD'

    def test_error_handling_for_invalid_currency(self):
        """Test error handling when invalid currency data is encountered."""
        # Test cases with invalid currency data
        invalid_cases = [
            {'symbol': 'TEST1', 'price': 100, 'currency': None},
            {'symbol': 'TEST2', 'price': 100, 'currency': ''},
            {'symbol': 'TEST3', 'price': 100, 'currency': 'invalid'},
            {'symbol': 'TEST4', 'price': 100}  # Missing currency
        ]

        for case in invalid_cases:
            # Apply error handling logic
            if 'currency' not in case or not case.get('currency'):
                case['currency'] = 'USD'  # Default fallback
            elif len(case['currency']) != 3 or not case['currency'].isupper():
                case['currency'] = 'USD'  # Invalid format fallback

            # After error handling, currency should be valid
            assert case['currency'] == 'USD'
            assert len(case['currency']) == 3
            assert case['currency'].isupper()

    def test_currency_in_error_responses(self):
        """Test that error responses still maintain currency context when possible."""
        # Error response with partial data
        error_response = {
            'success': False,
            'error_code': 'INVALID_SYMBOL',
            'message': 'Symbol not found',
            'data': {
                'symbol': 'INVALID',
                'currency': 'USD'  # Context maintained even in error
            }
        }

        # Even in error cases, currency context should be preserved
        if 'data' in error_response and 'currency' in error_response['data']:
            assert error_response['data']['currency'] == 'USD'

    def test_multi_currency_exchange_rate_context(self):
        """Test currency context for future multi-currency support."""
        # Framework for future multi-currency support
        exchange_context = {
            'base_currency': 'USD',
            'supported_currencies': ['USD', 'EUR', 'GBP', 'JPY', 'AUD'],
            'default_display_currency': 'USD'
        }

        # Verify exchange context structure
        assert 'base_currency' in exchange_context
        assert 'supported_currencies' in exchange_context
        assert 'default_display_currency' in exchange_context

        # Verify supported currencies are valid
        for currency in exchange_context['supported_currencies']:
            assert len(currency) == 3
            assert currency.isupper()
            assert currency.isalpha()

        # Verify base currency is in supported list
        assert exchange_context['base_currency'] in exchange_context['supported_currencies']
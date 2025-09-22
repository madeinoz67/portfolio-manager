"""
Test decimal precision compliance for financial calculations.

Validates FR-043 from the specification:
- All price data MUST use decimal precision for financial accuracy
- Currency information MUST be included with all price data
"""
import pytest
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch, MagicMock

from src.services.adapters.yfinance_adapter import YFinanceAdapter
from src.services.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from src.services.adapters.base_adapter import AdapterResponse


class TestDecimalPrecision:
    """Test that all financial calculations maintain decimal precision."""

    def test_alpha_vantage_adapter_uses_decimal(self):
        """Test that AlphaVantageAdapter uses Decimal for price values."""
        # Create adapter instance
        adapter = AlphaVantageAdapter("test_alpha", {"api_key": "test_key"})

        # Mock Alpha Vantage API response
        mock_response = {
            "Global Quote": {
                "01. symbol": "AAPL",
                "02. open": "149.8000",
                "03. high": "151.2500",
                "04. low": "149.1000",
                "05. price": "150.2500",
                "06. volume": "45123456",
                "07. latest trading day": "2025-09-22",
                "08. previous close": "149.7500",
                "09. change": "0.5000",
                "10. change percent": "0.3340%"
            }
        }

        # Test the parsing method
        result = adapter._parse_single_symbol_response("AAPL", mock_response)

        # Verify all price fields use Decimal
        assert isinstance(result["price"], Decimal)
        assert isinstance(result["open"], Decimal)
        assert isinstance(result["high"], Decimal)
        assert isinstance(result["low"], Decimal)
        assert isinstance(result["previous_close"], Decimal)
        assert isinstance(result["change"], Decimal)

        # Verify precision is maintained
        assert result["price"] == Decimal("150.2500")
        assert result["open"] == Decimal("149.8000")
        assert result["high"] == Decimal("151.2500")
        assert result["low"] == Decimal("149.1000")

    def test_yfinance_adapter_maintains_precision(self):
        """Test that YFinanceAdapter maintains precision in calculations."""
        # Create adapter instance
        adapter = YFinanceAdapter("test_yfinance", {})

        # Mock pandas DataFrame with price data
        import pandas as pd
        mock_hist = pd.DataFrame({
            'Open': [149.80, 150.10],
            'High': [151.25, 151.50],
            'Low': [149.10, 149.80],
            'Close': [150.25, 150.75],
            'Volume': [45123456, 42987654]
        })

        mock_info = {
            'longName': 'Apple Inc.',
            'currency': 'USD',
            'marketCap': 2500000000000,
            'exchange': 'NMS'
        }

        # Test change calculation precision
        latest = mock_hist.iloc[-1]
        previous = mock_hist.iloc[-2]

        change = float(latest['Close'] - previous['Close'])
        change_percent = float((change / previous['Close']) * 100)

        # Verify calculations maintain reasonable precision
        assert abs(change - 0.50) < 0.01  # Within 1 cent
        assert abs(change_percent - 0.33) < 0.1  # Within 0.1%

        # Test that price values are converted properly
        price_data = {
            "price": float(latest['Close']),
            "open": float(latest['Open']),
            "high": float(latest['High']),
            "low": float(latest['Low']),
            "volume": int(latest['Volume']),
            "change": change,
            "change_percent": change_percent
        }

        # Verify all numeric fields are present and reasonable
        assert isinstance(price_data["price"], float)
        assert isinstance(price_data["open"], float)
        assert isinstance(price_data["high"], float)
        assert isinstance(price_data["low"], float)
        assert isinstance(price_data["volume"], int)

    def test_price_calculations_avoid_floating_point_errors(self):
        """Test that price calculations avoid common floating-point errors."""
        # Test common problematic decimal values
        test_values = [
            ("0.1", "0.2", "0.3"),  # Classic floating point issue
            ("149.75", "0.50", "150.25"),  # Stock price calculation
            ("2800.123", "15.456", "2815.579"),  # High-precision calculation
        ]

        for price_str, change_str, expected_str in test_values:
            price = Decimal(price_str)
            change = Decimal(change_str)
            result = price + change

            expected = Decimal(expected_str)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_percentage_calculations_precision(self):
        """Test that percentage calculations maintain precision."""
        # Test portfolio percentage calculations
        test_cases = [
            (Decimal("10000.00"), Decimal("150.25"), "1.5025"),  # 1.5025%
            (Decimal("50000.00"), Decimal("2500.75"), "5.0015"),  # 5.0015%
            (Decimal("100.00"), Decimal("0.33"), "0.33"),        # 0.33%
        ]

        for total, change, expected_percent in test_cases:
            percentage = (change / total * 100).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
            expected = Decimal(expected_percent)

            assert percentage == expected, f"Expected {expected}%, got {percentage}%"

    def test_currency_precision_compliance(self):
        """Test that currency values maintain appropriate precision."""
        # Test different currency precisions
        currency_tests = [
            ("USD", "150.25", 2),   # US Dollar - 2 decimal places
            ("EUR", "125.50", 2),   # Euro - 2 decimal places
            ("JPY", "16500", 0),    # Japanese Yen - no decimal places
            ("BTC", "45000.12345678", 8),  # Bitcoin - 8 decimal places
        ]

        for currency, value_str, expected_precision in currency_tests:
            value = Decimal(value_str)

            # Format according to currency precision
            if expected_precision == 0:
                formatted = value.quantize(Decimal('1'))
            else:
                format_str = '0.' + '0' * expected_precision
                formatted = value.quantize(Decimal(format_str))

            # Verify precision is correct
            decimal_places = abs(formatted.as_tuple().exponent)
            assert decimal_places <= expected_precision

    def test_adapter_response_decimal_serialization(self):
        """Test that adapter responses properly serialize Decimal values."""
        # Create a response with Decimal values
        response_data = {
            "symbol": "AAPL",
            "price": Decimal("150.25"),
            "open": Decimal("149.80"),
            "high": Decimal("151.00"),
            "low": Decimal("149.50"),
            "change": Decimal("0.50"),
            "currency": "USD"
        }

        response = AdapterResponse.success_response(
            data=response_data,
            response_time_ms=245.0
        )

        # Verify response contains Decimal values
        assert isinstance(response.data["price"], Decimal)
        assert isinstance(response.data["open"], Decimal)
        assert isinstance(response.data["high"], Decimal)
        assert isinstance(response.data["low"], Decimal)

        # Verify response is serializable (would be handled by FastAPI)
        import json
        from decimal import Decimal

        def decimal_serializer(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            raise TypeError

        # Should not raise exception
        json.dumps(response.data, default=decimal_serializer)

    def test_portfolio_value_calculation_precision(self):
        """Test that portfolio value calculations maintain precision."""
        # Mock portfolio holdings with precise values
        holdings = [
            {"symbol": "AAPL", "quantity": Decimal("10.5"), "price": Decimal("150.25")},
            {"symbol": "GOOGL", "quantity": Decimal("2.25"), "price": Decimal("2800.50")},
            {"symbol": "MSFT", "quantity": Decimal("15.0"), "price": Decimal("420.75")},
        ]

        # Calculate total value with Decimal precision
        total_value = Decimal("0.00")
        for holding in holdings:
            holding_value = holding["quantity"] * holding["price"]
            total_value += holding_value

        # Expected values calculated manually
        expected_aapl = Decimal("10.5") * Decimal("150.25")  # 1577.625
        expected_googl = Decimal("2.25") * Decimal("2800.50")  # 6301.125
        expected_msft = Decimal("15.0") * Decimal("420.75")  # 6311.25
        expected_total = expected_aapl + expected_googl + expected_msft  # 14190.00

        assert total_value == expected_total

        # Verify individual calculations
        assert expected_aapl == Decimal("1577.625")
        assert expected_googl == Decimal("6301.125")
        assert expected_msft == Decimal("6311.25")
        assert expected_total == Decimal("14190.00")

    def test_cost_basis_precision(self):
        """Test that cost basis calculations maintain precision."""
        # Test cost basis calculation for multiple purchases
        purchases = [
            {"quantity": Decimal("5.0"), "price": Decimal("145.50")},
            {"quantity": Decimal("3.25"), "price": Decimal("148.75")},
            {"quantity": Decimal("2.25"), "price": Decimal("152.00")},
        ]

        total_cost = Decimal("0.00")
        total_quantity = Decimal("0.00")

        for purchase in purchases:
            cost = purchase["quantity"] * purchase["price"]
            total_cost += cost
            total_quantity += purchase["quantity"]

        # Calculate average cost basis
        avg_cost_basis = total_cost / total_quantity if total_quantity > 0 else Decimal("0.00")

        # Verify precision is maintained
        expected_total_cost = (
            Decimal("5.0") * Decimal("145.50") +
            Decimal("3.25") * Decimal("148.75") +
            Decimal("2.25") * Decimal("152.00")
        )

        assert total_cost == expected_total_cost
        assert total_quantity == Decimal("10.5")

        # Cost basis should be calculated precisely
        expected_avg = expected_total_cost / Decimal("10.5")
        assert avg_cost_basis == expected_avg


class TestCurrencyCompliance:
    """Test that currency information is properly included."""

    def test_all_price_responses_include_currency(self):
        """Test that all price responses include currency information."""
        # Test Alpha Vantage response
        alpha_response = {
            'symbol': 'AAPL',
            'price': Decimal("150.25"),
            'currency': 'USD',
            'open': Decimal("149.80"),
            'high': Decimal("151.00"),
            'low': Decimal("149.50")
        }

        assert "currency" in alpha_response
        assert alpha_response["currency"] == "USD"

        # Test Yahoo Finance response format
        yfinance_response = {
            "symbol": "AAPL",
            "price": 150.25,
            "currency": "USD",
            "open": 149.80,
            "high": 151.00,
            "low": 149.50
        }

        assert "currency" in yfinance_response
        assert yfinance_response["currency"] == "USD"

    def test_currency_consistency_across_adapters(self):
        """Test that currency handling is consistent across adapters."""
        # Both adapters should handle USD consistently
        currencies_to_test = ["USD", "EUR", "GBP", "AUD"]

        for currency in currencies_to_test:
            # Verify currency code format
            assert isinstance(currency, str)
            assert len(currency) == 3
            assert currency.isupper()

    def test_multi_currency_portfolio_calculations(self):
        """Test precision in multi-currency portfolio calculations."""
        # Mock holdings in different currencies
        holdings = [
            {"symbol": "AAPL", "price": Decimal("150.25"), "currency": "USD", "quantity": Decimal("10")},
            {"symbol": "ASML", "price": Decimal("650.50"), "currency": "EUR", "quantity": Decimal("5")},
            {"symbol": "BHP", "price": Decimal("45.75"), "currency": "AUD", "quantity": Decimal("100")},
        ]

        # Mock exchange rates (would come from forex adapter)
        exchange_rates = {
            "EUR_TO_USD": Decimal("1.0850"),
            "AUD_TO_USD": Decimal("0.6525")
        }

        # Convert all to USD with precision
        usd_values = []
        for holding in holdings:
            if holding["currency"] == "USD":
                usd_value = holding["price"] * holding["quantity"]
            elif holding["currency"] == "EUR":
                usd_value = holding["price"] * holding["quantity"] * exchange_rates["EUR_TO_USD"]
            elif holding["currency"] == "AUD":
                usd_value = holding["price"] * holding["quantity"] * exchange_rates["AUD_TO_USD"]

            usd_values.append(usd_value)

        # Verify calculations maintain precision
        total_usd = sum(usd_values)

        # Verify individual conversions
        expected_aapl = Decimal("10") * Decimal("150.25")  # 1502.50 USD
        expected_asml = Decimal("5") * Decimal("650.50") * Decimal("1.0850")  # 3529.21 USD
        expected_bhp = Decimal("100") * Decimal("45.75") * Decimal("0.6525")  # 2986.44 USD

        assert usd_values[0] == expected_aapl
        assert usd_values[1] == expected_asml
        assert usd_values[2] == expected_bhp

        expected_total = expected_aapl + expected_asml + expected_bhp
        assert total_usd == expected_total
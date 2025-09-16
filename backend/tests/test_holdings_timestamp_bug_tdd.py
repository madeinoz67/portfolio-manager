"""
TDD test for holdings timestamp bug fix.

The issue is that StockResponse.convert_timestamp() is being called on
data that already has string timestamps, causing AttributeError: 'str' object has no attribute 'tzinfo'
"""

import pytest
from datetime import datetime, timezone
from src.schemas.stock import StockResponse
from src.utils.datetime_utils import to_iso_string


def test_convert_timestamp_handles_string_input():
    """
    Test that convert_timestamp validator can handle string input.

    BUG: When last_price_update is already a string (ISO format),
    the validator should not attempt to convert it again.
    """
    # Test data where last_price_update is already a string
    iso_string = "2025-09-16T04:24:23.882883Z"

    data_dict = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'exchange': 'ASX',
        'current_price': 100.50,
        'last_price_update': iso_string  # Already a string!
    }

    # This should NOT raise AttributeError: 'str' object has no attribute 'tzinfo'
    stock_response = StockResponse.model_validate(data_dict)

    # The string should remain unchanged
    assert stock_response.last_price_update == iso_string


def test_convert_timestamp_handles_datetime_input():
    """
    Test that convert_timestamp validator can handle datetime input.

    This should continue to work as before.
    """
    # Test data where last_price_update is a datetime object
    test_datetime = datetime(2025, 9, 16, 4, 24, 23, tzinfo=timezone.utc)

    data_dict = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'exchange': 'ASX',
        'current_price': 100.50,
        'last_price_update': test_datetime  # datetime object
    }

    # This should work and convert datetime to string
    stock_response = StockResponse.model_validate(data_dict)

    # Should be converted to ISO string format
    expected_string = to_iso_string(test_datetime)
    assert stock_response.last_price_update == expected_string


def test_convert_timestamp_handles_none_input():
    """
    Test that convert_timestamp validator can handle None input.
    """
    data_dict = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'exchange': 'ASX',
        'current_price': 100.50,
        'last_price_update': None  # None value
    }

    # This should work
    stock_response = StockResponse.model_validate(data_dict)

    # Should remain None
    assert stock_response.last_price_update is None


def test_convert_timestamp_handles_missing_field():
    """
    Test that convert_timestamp validator handles missing field gracefully.
    """
    data_dict = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'symbol': 'TEST',
        'company_name': 'Test Company',
        'exchange': 'ASX',
        'current_price': 100.50,
        # last_price_update is missing
    }

    # This should work with default None
    stock_response = StockResponse.model_validate(data_dict)

    # Should be None by default
    assert stock_response.last_price_update is None


def test_holdings_api_integration():
    """
    Integration test that simulates the failing holdings API scenario.

    This reproduces the actual error from the holdings endpoint.
    """
    # This simulates the data structure from holdings API where
    # the timestamp comes from a SQLAlchemy object that's already been processed
    holding_dict = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'portfolio_id': '456e7890-e89b-12d3-a456-426614174000',
        'stock_id': '789e1234-e89b-12d3-a456-426614174000',
        'quantity': 100,
        'average_cost': 95.00,
        'current_value': 10050.00,
        'unrealized_gain_loss': 550.00,
        'unrealized_gain_loss_percent': 5.79,
        'recent_news_count': 0,
        'stock': {
            'id': '789e1234-e89b-12d3-a456-426614174000',
            'symbol': 'CBA',
            'company_name': 'Commonwealth Bank',
            'exchange': 'ASX',
            'current_price': 100.50,
            'daily_change': 2.50,
            'daily_change_percent': 2.55,
            'status': 'ACTIVE',
            'last_price_update': '2025-09-16T04:24:23.882883Z'  # STRING!
        }
    }

    # Extract stock data - this is where the error occurs
    stock_data = holding_dict['stock']

    # This should NOT raise AttributeError: 'str' object has no attribute 'tzinfo'
    stock_response = StockResponse.model_validate(stock_data)

    # Timestamp should remain as string
    assert stock_response.last_price_update == '2025-09-16T04:24:23.882883Z'
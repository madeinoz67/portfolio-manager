"""
Market Data Adapter Framework.

This package provides a standardized adapter pattern for integrating
multiple market data providers with consistent interface, metrics tracking,
and configuration management.
"""

from .base_adapter import MarketDataAdapter, AdapterResponse, AdapterError
from .registry import ProviderRegistry

__all__ = [
    "MarketDataAdapter",
    "AdapterResponse",
    "AdapterError",
    "ProviderRegistry",
]
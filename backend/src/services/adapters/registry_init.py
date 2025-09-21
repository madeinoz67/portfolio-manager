"""
Registry initialization for market data provider adapters.

Registers all available adapter implementations with the global registry.
"""

import logging
from .registry import get_provider_registry, register_provider
from .yfinance_adapter import YFinanceAdapter
from .alpha_vantage_adapter import AlphaVantageAdapter

logger = logging.getLogger(__name__)


def initialize_adapter_registry() -> None:
    """
    Initialize the adapter registry with all available providers.

    This function should be called during application startup to register
    all adapter implementations with the global registry.
    """
    registry = get_provider_registry()

    # Register Yahoo Finance adapter
    register_provider(
        adapter_class=YFinanceAdapter,
        provider_name="yfinance",
        display_name="Yahoo Finance",
        description="Free market data from Yahoo Finance with support for real-time quotes and bulk requests",
        version="1.0.0",
        is_enabled=True
    )

    # Register Alpha Vantage adapter
    register_provider(
        adapter_class=AlphaVantageAdapter,
        provider_name="alpha_vantage",
        display_name="Alpha Vantage",
        description="Professional market data from Alpha Vantage with detailed fundamentals and technical indicators",
        version="1.0.0",
        is_enabled=True
    )

    logger.info(f"Adapter registry initialized with {len(registry.get_available_provider_names())} providers")


def get_registered_providers_summary() -> dict:
    """
    Get a summary of all registered providers.

    Returns:
        Dictionary with provider summary information
    """
    registry = get_provider_registry()
    providers = registry.list_providers()

    return {
        "total_providers": len(providers),
        "enabled_providers": len([p for p in providers if p.is_enabled]),
        "providers": [
            {
                "name": p.provider_name,
                "display_name": p.display_name,
                "description": p.description,
                "version": p.version,
                "enabled": p.is_enabled
            }
            for p in providers
        ]
    }
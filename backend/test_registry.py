#!/usr/bin/env python3
"""
Test script to check what providers are registered in the adapter registry.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.services.adapters.registry import get_provider_registry
from src.services.adapters.registry_init import initialize_adapter_registry

async def test_registry():
    """Test what providers are registered."""
    print("=== Testing Provider Registry ===")

    # Initialize the adapter registry first
    print("Initializing adapter registry...")
    initialize_adapter_registry()

    # Get provider registry
    registry = get_provider_registry()

    # Check registered providers
    providers = registry.list_providers()
    print(f"Total registered providers: {len(providers)}")

    for info in providers:
        print(f"  - {info.provider_name}: {info.display_name} v{info.version}")
        print(f"    Enabled: {info.is_enabled}")
        print(f"    Description: {info.description}")

    # Test specific provider lookup
    print(f"\nTesting specific provider lookups:")
    for provider_name in ["yfinance", "alpha_vantage", "yahoo_finance"]:
        is_registered = registry.is_provider_registered(provider_name)
        print(f"  - {provider_name}: {'✅ Registered' if is_registered else '❌ Not registered'}")

        if is_registered:
            info = registry.get_provider_info(provider_name)
            print(f"    Info: {info.display_name} v{info.version}")

if __name__ == "__main__":
    asyncio.run(test_registry())
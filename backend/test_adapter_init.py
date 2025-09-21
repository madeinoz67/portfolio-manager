#!/usr/bin/env python3
"""
Simple test script to debug adapter initialization issues.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.services.adapters.registry import get_provider_registry
from src.services.adapters.registry_init import initialize_adapter_registry
from src.database import get_db
from src.models.provider_configuration import ProviderConfiguration

async def test_adapter_initialization():
    """Test adapter initialization to see detailed error logging."""
    print("=== Testing Adapter Initialization ===")

    # Initialize the adapter registry first
    print("Initializing adapter registry...")
    initialize_adapter_registry()

    # Get database session
    db = next(get_db())

    # Get provider configurations
    configs = db.query(ProviderConfiguration).filter(
        ProviderConfiguration.is_active == 1
    ).all()

    print(f"Found {len(configs)} active provider configurations:")
    for config in configs:
        print(f"  - {config.provider_name}: {config.display_name}")

    # Get provider registry
    registry = get_provider_registry()

    # Test each provider
    for config in configs:
        print(f"\n=== Testing {config.provider_name} ===")

        # Try to create adapter instance
        try:
            print(f"Creating adapter instance for {config.provider_name}...")
            adapter = await registry.create_provider_instance(
                config.provider_name,
                config.config_data
            )

            if adapter:
                print(f"✅ Successfully created {config.provider_name} adapter")

                # Test health check
                print(f"Testing health check...")
                health_response = await adapter.health_check()
                if health_response.success:
                    print(f"✅ Health check passed for {config.provider_name}")
                else:
                    print(f"❌ Health check failed for {config.provider_name}: {health_response.error_message}")

                # Cleanup
                await adapter.cleanup()

            else:
                print(f"❌ Failed to create {config.provider_name} adapter")

        except Exception as e:
            print(f"❌ Exception creating {config.provider_name} adapter: {e}")
            import traceback
            traceback.print_exc()

    # Close database
    db.close()

if __name__ == "__main__":
    asyncio.run(test_adapter_initialization())
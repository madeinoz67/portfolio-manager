#!/usr/bin/env python3
"""Test the yfinance adapter directly to debug the issue."""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_adapter():
    try:
        from services.adapters.yfinance_adapter import YFinanceAdapter

        print("Testing YFinanceAdapter directly...")

        # Create adapter instance with empty config
        config = {}
        adapter = YFinanceAdapter("test_provider", config)

        # Initialize
        await adapter.initialize()
        print("Adapter initialized successfully")

        # Test single symbol
        symbols = ['CBA.AX']
        print(f"Testing symbols: {symbols}")

        response = await adapter.fetch_prices(symbols)
        print(f"Response success: {response.success}")
        print(f"Response data: {response.data}")
        print(f"Response error: {response.error}")

        if response.success and response.data:
            for symbol, data in response.data.items():
                if data:
                    print(f"SUCCESS: {symbol} = ${data.get('price', 'N/A')}")
                else:
                    print(f"FAIL: {symbol} = No data")
        else:
            print(f"ADAPTER FAILED: {response.error}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_adapter())
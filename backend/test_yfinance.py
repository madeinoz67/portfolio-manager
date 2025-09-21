#!/usr/bin/env python3
"""Test yfinance with Australian symbols to debug nan issue."""

import yfinance as yf
import pandas as pd

def test_yfinance_symbols():
    symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'CSL.AX', 'BHP.AX']
    print("Testing yfinance with Australian symbols...")

    for symbol in symbols:
        try:
            print(f"\n--- Testing {symbol} ---")
            ticker = yf.Ticker(symbol)

            # Test different methods
            print("Method 1: history(period='1d')")
            data = ticker.history(period='1d')
            if data.empty:
                print(f"  {symbol}: No data from history()")
            else:
                latest = data.iloc[-1]
                print(f"  {symbol}: Close=${latest['Close']:.2f}")

            print("Method 2: info")
            info = ticker.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            print(f"  {symbol}: Current price from info = {current_price}")

            print("Method 3: download()")
            download_data = yf.download(symbol, period='1d', progress=False)
            if download_data.empty:
                print(f"  {symbol}: No data from download()")
            else:
                latest_download = download_data.iloc[-1]
                print(f"  {symbol}: Close from download=${latest_download['Close']:.2f}")

        except Exception as e:
            print(f"  {symbol}: Error - {e}")

if __name__ == "__main__":
    test_yfinance_symbols()
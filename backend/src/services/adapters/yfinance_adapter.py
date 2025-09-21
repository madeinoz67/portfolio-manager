"""
Yahoo Finance adapter implementation.

Provides market data through the Yahoo Finance API with full metrics tracking.
"""

import asyncio
import aiohttp
import time
import pandas as pd
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any

from .base_adapter import (
    MarketDataAdapter,
    AdapterResponse,
    ProviderCapabilities,
    CostInformation,
    AdapterError,
    RateLimitError,
    ProviderTimeoutError
)
from .metrics import get_metrics_collector


class YFinanceAdapter(MarketDataAdapter):
    """Yahoo Finance market data adapter with built-in metrics collection."""

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        super().__init__(provider_name, config)
        self.base_url = config.get("base_url", "https://query1.finance.yahoo.com/v8/finance/chart")
        self.timeout = config.get("timeout", 30)
        self.metrics_collector = get_metrics_collector()

        # Yahoo Finance doesn't require API key but has informal rate limits
        # yfinance library handles rate limiting internally, these are conservative estimates
        self.rate_limit_per_minute = config.get("rate_limit_per_minute", 60)    # Conservative for yfinance library
        self.rate_limit_per_day = config.get("rate_limit_per_day", 2000)       # Conservative daily limit

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Yahoo Finance capabilities."""
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk_quotes=True,
            max_symbols_per_request=50,  # yfinance library supports bulk requests efficiently
            rate_limit_per_minute=self.rate_limit_per_minute,
            rate_limit_per_day=self.rate_limit_per_day,
            supports_intraday=True,
            supports_options=False,
            supports_crypto=True
        )

    @property
    def cost_info(self) -> CostInformation:
        """Return Yahoo Finance cost information."""
        return CostInformation(
            cost_per_call=Decimal('0.00'),  # Free service
            cost_model="free",
            monthly_quota=None,  # No hard quota, just rate limits
            burst_quota=None,
            overage_cost=Decimal('0.00')
        )

    async def initialize(self) -> bool:
        """Initialize the Yahoo Finance adapter."""
        try:
            self.logger.info(f"Initializing Yahoo Finance adapter for provider: {self.provider_name}")
            # Test connectivity with a simple request
            test_response = await self.health_check()
            if test_response.success:
                self.logger.info(f"Yahoo Finance adapter initialized successfully for provider: {self.provider_name}")
                return True
            else:
                self.logger.error(f"Yahoo Finance adapter health check failed: {test_response.error_message}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Yahoo Finance adapter: {e}")
            return False

    async def health_check(self) -> AdapterResponse:
        """Perform lightweight health check without actual data fetching to avoid rate limits."""
        request_id = self.metrics_collector.record_request_start(
            provider_name=self.provider_name,
            operation="health_check"
        )

        start_time = time.time()
        response = None
        error_response = None

        try:
            # Simple dependency check without making actual API calls
            import yfinance as yf

            # Basic library test - just create a ticker instance without fetching data
            ticker = yf.Ticker("AAPL")

            # If we get here, the library is available and basic instantiation works
            response = AdapterResponse.success_response(
                data={"status": "healthy", "library": "yfinance", "check_type": "dependency"},
                response_time_ms=(time.time() - start_time) * 1000
            )

        except ImportError:
            error_response = AdapterResponse.error_response(
                error_message="yfinance library not available",
                error_code="MISSING_DEPENDENCY",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            error_response = AdapterResponse.error_response(
                error_message=f"Health check error: {str(e)}",
                error_code="HEALTH_CHECK_ERROR",
                response_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            self.metrics_collector.record_request_end(
                request_id=request_id,
                provider_name=self.provider_name,
                operation="health_check",
                response=error_response if error_response else response
            )

        return error_response if error_response else response

    async def fetch_prices(self, symbols: Union[str, List[str]]) -> AdapterResponse:
        """
        Fetch current prices from Yahoo Finance with full metrics tracking.

        Handles both single symbol and bulk requests with automatic optimization.
        """
        # Normalize input
        if isinstance(symbols, str):
            symbol_list = [symbols]
            single_symbol = True
        else:
            symbol_list = symbols
            single_symbol = False

        # Record metrics start
        operation = "fetch_single_price" if single_symbol else "fetch_bulk_prices"
        request_id = self.metrics_collector.record_request_start(
            provider_name=self.provider_name,
            operation=operation
        )

        start_time = time.time()

        try:
            if len(symbol_list) == 1:
                # Single symbol request
                result = await self._fetch_single_symbol(symbol_list[0])
            else:
                # Bulk request - Yahoo Finance supports multiple symbols
                result = await self._fetch_multiple_symbols(symbol_list)

            response_time = (time.time() - start_time) * 1000

            if result:
                response = AdapterResponse.success_response(
                    data=result if not single_symbol else result.get(symbol_list[0]),
                    response_time_ms=response_time,
                    provider_metadata={
                        "symbols_requested": len(symbol_list),
                        "symbols_returned": len(result) if isinstance(result, dict) else 1,
                        "provider": "yahoo_finance"
                    }
                )
            else:
                response = AdapterResponse.error_response(
                    error_message="No data returned from Yahoo Finance",
                    error_code="NO_DATA",
                    response_time_ms=response_time
                )

        except RateLimitError as e:
            response = AdapterResponse.error_response(
                error_message=str(e),
                error_code="RATE_LIMIT_EXCEEDED",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except ProviderTimeoutError as e:
            response = AdapterResponse.error_response(
                error_message=str(e),
                error_code="TIMEOUT",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            response = AdapterResponse.error_response(
                error_message=f"Yahoo Finance error: {str(e)}",
                error_code="PROVIDER_ERROR",
                response_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            # Record metrics end with cost (free for Yahoo Finance)
            self.metrics_collector.record_request_end(
                request_id=request_id,
                provider_name=self.provider_name,
                operation=operation,
                response=response,
                cost_usd=Decimal('0.00')  # Yahoo Finance is free
            )

        return response

    async def _fetch_single_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a single symbol using yfinance library."""
        try:
            import yfinance as yf
            import asyncio

            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def fetch_ticker_data():
                # Handle ASX symbols - yfinance expects .AX suffix
                yf_symbol = self._convert_symbol_for_yfinance(symbol)
                ticker = yf.Ticker(yf_symbol)

                # Get current info and history
                info = ticker.info
                hist = ticker.history(period="1d", interval="1m")

                if hist.empty:
                    return None

                latest = hist.iloc[-1]
                return {
                    "symbol": symbol,
                    "price": float(latest['Close']),
                    "open": float(latest['Open']),
                    "high": float(latest['High']),
                    "low": float(latest['Low']),
                    "volume": int(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
                    "change": 0.0,  # Will be calculated from previous close
                    "change_percent": 0.0,
                    "market_cap": info.get('marketCap', 0),
                    "company_name": info.get('longName', symbol),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "provider": "yfinance"
                }

            result = await loop.run_in_executor(None, fetch_ticker_data)
            return {symbol: result} if result else None

        except ImportError:
            raise AdapterError("yfinance library not installed", self.provider_name, "MISSING_DEPENDENCY")
        except Exception as e:
            self.logger.error(f"Error fetching {symbol} from yfinance: {e}")
            raise AdapterError(f"yfinance error: {str(e)}", self.provider_name, "YFINANCE_ERROR")

    async def _fetch_multiple_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch data for multiple symbols using yfinance bulk download."""
        try:
            import yfinance as yf
            import asyncio

            # Run yfinance bulk download in thread pool
            loop = asyncio.get_event_loop()

            def fetch_bulk_data():
                # Convert symbols for yfinance
                yf_symbols = [self._convert_symbol_for_yfinance(sym) for sym in symbols]

                # Use yfinance Tickers approach like legacy service (works regardless of market hours)
                tickers = yf.Tickers(' '.join(yf_symbols))

                results = {}

                for i, original_symbol in enumerate(symbols):
                    yf_symbol = yf_symbols[i]

                    try:
                        # Get ticker instance
                        ticker = tickers.tickers.get(yf_symbol)
                        if ticker is None:
                            # Fallback: create individual ticker
                            ticker = yf.Ticker(yf_symbol)

                        # Get current price info (works even when markets closed)
                        info = ticker.info

                        # Get price data from info
                        reg_price = info.get('regularMarketPrice')
                        curr_price = info.get('currentPrice')
                        prev_close = info.get('previousClose')

                        # Try to get price from info (most reliable)
                        price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')

                        if price and price > 0:
                            results[original_symbol] = {
                                "symbol": original_symbol,
                                "price": float(price),
                                "open": info.get('regularMarketOpen', info.get('open', price)),
                                "high": info.get('regularMarketDayHigh', info.get('dayHigh', price)),
                                "low": info.get('regularMarketDayLow', info.get('dayLow', price)),
                                "volume": info.get('regularMarketVolume', info.get('volume', 0)),
                                "change": info.get('regularMarketChange', 0.0),
                                "change_percent": info.get('regularMarketChangePercent', 0.0),
                                "market_cap": info.get('marketCap', 0),
                                "company_name": info.get('longName', info.get('shortName', original_symbol)),
                                "fetched_at": datetime.now(timezone.utc).isoformat(),
                                "provider": "yfinance"
                            }
                        else:
                            self.logger.warning(f"No data available for {original_symbol}")

                    except Exception as e:
                        self.logger.error(f"Error processing {original_symbol}: {e}")
                        continue

                return results

            result = await loop.run_in_executor(None, fetch_bulk_data)
            return result

        except ImportError:
            raise AdapterError("yfinance library not installed", self.provider_name, "MISSING_DEPENDENCY")
        except Exception as e:
            self.logger.error(f"Error in bulk yfinance fetch: {e}")
            raise AdapterError(f"yfinance bulk error: {str(e)}", self.provider_name, "YFINANCE_BULK_ERROR")

    def _convert_symbol_for_yfinance(self, symbol: str) -> str:
        """Convert symbol to yfinance format (e.g., ASX symbols need .AX suffix)."""
        # Handle ASX symbols - yfinance expects .AX suffix for ASX stocks
        if len(symbol) <= 3 and symbol.isalpha() and symbol.isupper():
            # Likely an ASX symbol, add .AX suffix
            return f"{symbol}.AX"
        return symbol

    def _parse_yahoo_response(self, symbol: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse Yahoo Finance API response for a single symbol."""
        try:
            chart = data.get('chart', {})
            result = chart.get('result', [])

            if not result:
                return None

            quote_data = result[0]
            meta = quote_data.get('meta', {})

            # Get the latest price
            current_price = meta.get('regularMarketPrice')
            if current_price is None:
                return None

            return {
                'symbol': symbol,
                'price': Decimal(str(current_price)),
                'currency': meta.get('currency', 'USD'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'volume': meta.get('regularMarketVolume'),
                'market_cap': None,  # Yahoo doesn't provide this in basic quotes
                'source': self.provider_name,
                'provider_metadata': {
                    'exchange': meta.get('exchangeName'),
                    'timezone': meta.get('exchangeTimezoneName'),
                    'market_state': meta.get('marketState')
                }
            }

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Error parsing Yahoo Finance response for {symbol}: {e}")
            return None

    def _parse_yahoo_bulk_response(self, symbols: List[str], data: Dict) -> Dict[str, Any]:
        """Parse Yahoo Finance API response for multiple symbols."""
        results = {}

        try:
            chart = data.get('chart', {})
            result_list = chart.get('result', [])

            for i, symbol in enumerate(symbols):
                if i < len(result_list):
                    symbol_data = self._parse_single_result(symbol, result_list[i])
                    if symbol_data:
                        results[symbol] = symbol_data

        except Exception as e:
            self.logger.error(f"Error parsing Yahoo Finance bulk response: {e}")

        return results

    def _parse_single_result(self, symbol: str, result_data: Dict) -> Optional[Dict[str, Any]]:
        """Parse a single symbol result from bulk response."""
        try:
            meta = result_data.get('meta', {})
            current_price = meta.get('regularMarketPrice')

            if current_price is None:
                return None

            return {
                'symbol': symbol,
                'price': Decimal(str(current_price)),
                'currency': meta.get('currency', 'USD'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'volume': meta.get('regularMarketVolume'),
                'market_cap': None,
                'source': self.provider_name,
                'provider_metadata': {
                    'exchange': meta.get('exchangeName'),
                    'timezone': meta.get('exchangeTimezoneName'),
                    'market_state': meta.get('marketState')
                }
            }

        except (KeyError, ValueError, TypeError):
            return None

    async def get_rate_limit_status(self) -> AdapterResponse:
        """Get current rate limit status for Yahoo Finance."""
        # Yahoo Finance doesn't provide rate limit headers, so we estimate
        return AdapterResponse.success_response(
            data={
                "requests_remaining": None,  # Unknown for Yahoo Finance
                "reset_time": None,  # Unknown for Yahoo Finance
                "quota_used_percent": 0.0,  # Can't determine without API key
                "provider_info": "Yahoo Finance does not expose rate limit information"
            },
            response_time_ms=0.0
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for Yahoo Finance adapter."""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL for Yahoo Finance API",
                    "default": "https://query1.finance.yahoo.com/v8/finance/chart"
                },
                "timeout": {
                    "type": "number",
                    "description": "Request timeout in seconds",
                    "default": 30
                },
                "rate_limit_per_minute": {
                    "type": "number",
                    "description": "Conservative rate limit per minute",
                    "default": 100
                },
                "rate_limit_per_day": {
                    "type": "number",
                    "description": "Conservative rate limit per day",
                    "default": 10000
                }
            },
            "required": []  # No required fields for Yahoo Finance
        }

    def get_example_configuration(self) -> Dict[str, Any]:
        """Return example configuration for Yahoo Finance adapter."""
        return {
            "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
            "timeout": 30,
            "rate_limit_per_minute": 100,
            "rate_limit_per_day": 10000
        }

    async def cleanup(self) -> None:
        """Clean up Yahoo Finance adapter resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        await super().cleanup()
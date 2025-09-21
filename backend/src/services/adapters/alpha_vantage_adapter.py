"""
Alpha Vantage adapter implementation.

Provides market data through the Alpha Vantage API with full metrics tracking and cost calculation.
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
    AuthenticationError,
    ProviderTimeoutError
)
from .metrics import get_metrics_collector


class AlphaVantageAdapter(MarketDataAdapter):
    """Alpha Vantage market data adapter with built-in metrics collection."""

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        super().__init__(provider_name, config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://www.alphavantage.co/query")
        self.timeout = config.get("timeout", 30)
        self.metrics_collector = get_metrics_collector()

        # Alpha Vantage rate limits (realistic values)
        # Free tier: 25 requests per day, Premium: 5 requests per minute
        self.tier = config.get("tier", "free")  # "free" or "premium"

        if self.tier == "free":
            self.rate_limit_per_minute = config.get("rate_limit_per_minute", 1)   # Conservative for free tier
            self.rate_limit_per_day = config.get("rate_limit_per_day", 25)       # Free tier daily limit
        else:
            self.rate_limit_per_minute = config.get("rate_limit_per_minute", 5)   # Premium tier
            self.rate_limit_per_day = config.get("rate_limit_per_day", 500)      # Premium tier daily

        if not self.api_key:
            raise AuthenticationError("Alpha Vantage API key is required", self.provider_name, "MISSING_API_KEY")

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Alpha Vantage capabilities."""
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk_quotes=False,  # Alpha Vantage doesn't support bulk requests in free tier
            max_symbols_per_request=1,
            rate_limit_per_minute=self.rate_limit_per_minute,
            rate_limit_per_day=self.rate_limit_per_day,
            supports_intraday=True,
            supports_options=False,
            supports_crypto=True
        )

    @property
    def cost_info(self) -> CostInformation:
        """Return Alpha Vantage cost information."""
        # Costs vary by plan - this assumes free tier
        return CostInformation(
            cost_per_call=Decimal('0.00'),  # Free tier
            cost_model="freemium",
            monthly_quota=500,  # Free tier monthly quota
            burst_quota=5,      # 5 requests per minute
            overage_cost=Decimal('0.00')  # Free tier has no overage
        )

    async def initialize(self) -> bool:
        """Initialize the Alpha Vantage adapter."""
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not provided")
            return False

        try:
            # Test connectivity with a simple request
            test_response = await self.health_check()
            return test_response.success
        except Exception as e:
            self.logger.error(f"Failed to initialize Alpha Vantage adapter: {e}")
            return False

    async def health_check(self) -> AdapterResponse:
        """Perform health check using AAPL as test symbol."""
        request_id = self.metrics_collector.record_request_start(
            provider_name=self.provider_name,
            operation="health_check"
        )

        start_time = time.time()

        try:
            response = await self.fetch_prices("AAPL")

            if response.success:
                return AdapterResponse.success_response(
                    data={"status": "healthy", "test_symbol": "AAPL"},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            else:
                return AdapterResponse.error_response(
                    error_message=f"Health check failed: {response.error_message}",
                    error_code="HEALTH_CHECK_FAILED",
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
                response=error_response if 'error_response' in locals() else response
            )

        return error_response if 'error_response' in locals() else response

    async def fetch_prices(self, symbols: Union[str, List[str]]) -> AdapterResponse:
        """
        Fetch current prices from Alpha Vantage with full metrics tracking.

        Note: Alpha Vantage doesn't support bulk requests, so multiple symbols
        are fetched sequentially with appropriate rate limiting.
        """
        # Normalize input
        if isinstance(symbols, str):
            symbol_list = [symbols]
            single_symbol = True
        else:
            symbol_list = symbols
            single_symbol = False

        # Record metrics start
        operation = "fetch_single_price" if single_symbol else "fetch_multiple_prices"
        request_id = self.metrics_collector.record_request_start(
            provider_name=self.provider_name,
            operation=operation
        )

        start_time = time.time()
        results = {}

        try:
            for symbol in symbol_list:
                symbol_result = await self._fetch_single_symbol(symbol)
                if symbol_result:
                    results[symbol] = symbol_result

                # Rate limiting for multiple symbols
                if len(symbol_list) > 1 and symbol != symbol_list[-1]:
                    if self.tier == "free":
                        await asyncio.sleep(60)  # 1 request per minute for free tier
                    else:
                        await asyncio.sleep(12)  # 5 requests per minute = 12 seconds between requests for premium

            response_time = (time.time() - start_time) * 1000

            if results:
                # Calculate cost based on number of API calls made
                cost_per_call = self.cost_info.cost_per_call
                total_cost = cost_per_call * len(results)

                response = AdapterResponse.success_response(
                    data=results if not single_symbol else results.get(symbol_list[0]),
                    response_time_ms=response_time,
                    provider_metadata={
                        "symbols_requested": len(symbol_list),
                        "symbols_returned": len(results),
                        "api_calls_made": len(results),
                        "cost_usd": str(total_cost),
                        "provider": "alpha_vantage"
                    }
                )
            else:
                response = AdapterResponse.error_response(
                    error_message="No data returned from Alpha Vantage",
                    error_code="NO_DATA",
                    response_time_ms=response_time
                )

        except RateLimitError as e:
            response = AdapterResponse.error_response(
                error_message=str(e),
                error_code="RATE_LIMIT_EXCEEDED",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except AuthenticationError as e:
            response = AdapterResponse.error_response(
                error_message=str(e),
                error_code="AUTHENTICATION_FAILED",
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
                error_message=f"Alpha Vantage error: {str(e)}",
                error_code="PROVIDER_ERROR",
                response_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            # Record metrics end with actual cost
            cost_usd = Decimal('0.00')
            if results:
                cost_usd = self.cost_info.cost_per_call * len(results)

            self.metrics_collector.record_request_end(
                request_id=request_id,
                provider_name=self.provider_name,
                operation=operation,
                response=response,
                cost_usd=cost_usd
            )

        return response

    async def _fetch_single_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a single symbol using alpha_vantage library."""
        try:
            from alpha_vantage.timeseries import TimeSeries
            import asyncio

            # Run alpha_vantage in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def fetch_alpha_vantage_data():
                ts = TimeSeries(key=self.api_key, output_format='pandas')

                try:
                    # Get daily time series data
                    data, meta_data = ts.get_daily(symbol=symbol)

                    if data.empty:
                        return None

                    # Get the most recent data point
                    latest = data.iloc[-1]

                    # Parse the response
                    return {
                        "symbol": symbol,
                        "price": float(latest['4. close']),
                        "open": float(latest['1. open']),
                        "high": float(latest['2. high']),
                        "low": float(latest['3. low']),
                        "volume": int(latest['5. volume']),
                        "change": 0.0,  # Calculate from previous close if available
                        "change_percent": 0.0,
                        "market_cap": 0,  # Alpha Vantage doesn't provide market cap in daily data
                        "company_name": symbol,  # Could enhance with company overview API
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "provider": "alpha_vantage"
                    }

                except Exception as e:
                    if "Thank you for using Alpha Vantage" in str(e) or "rate limit" in str(e).lower():
                        raise RateLimitError("Alpha Vantage rate limit exceeded", self.provider_name, "RATE_LIMIT")
                    elif "Invalid API call" in str(e) or "Invalid symbol" in str(e):
                        return None  # Symbol not found
                    else:
                        raise AdapterError(f"Alpha Vantage error: {str(e)}", self.provider_name, "AV_ERROR")

            result = await loop.run_in_executor(None, fetch_alpha_vantage_data)
            return {symbol: result} if result else None

        except ImportError:
            raise AdapterError("alpha_vantage library not installed", self.provider_name, "MISSING_DEPENDENCY")
        except Exception as e:
            self.logger.error(f"Error fetching {symbol} from Alpha Vantage: {e}")
            raise

    def _parse_alpha_vantage_response(self, symbol: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse Alpha Vantage API response."""
        try:
            # Check for API errors first
            if "Error Message" in data:
                raise AdapterError(data["Error Message"], self.provider_name, "API_ERROR")

            if "Note" in data:
                # Rate limit or API limit hit
                raise RateLimitError(data["Note"], self.provider_name, "RATE_LIMIT")

            # Parse Global Quote response
            quote = data.get("Global Quote", {})
            if not quote:
                return None

            # Alpha Vantage Global Quote format
            current_price = quote.get("05. price")
            if not current_price:
                return None

            return {
                'symbol': symbol,
                'price': Decimal(current_price),
                'currency': 'USD',  # Alpha Vantage default
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'volume': int(quote.get("06. volume", 0)) if quote.get("06. volume") else None,
                'market_cap': None,  # Not provided by Global Quote
                'source': self.provider_name,
                'provider_metadata': {
                    'open': quote.get("02. open"),
                    'high': quote.get("03. high"),
                    'low': quote.get("04. low"),
                    'previous_close': quote.get("08. previous close"),
                    'change': quote.get("09. change"),
                    'change_percent': quote.get("10. change percent"),
                    'latest_trading_day': quote.get("07. latest trading day")
                }
            }

        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Error parsing Alpha Vantage response for {symbol}: {e}")
            return None

    async def get_rate_limit_status(self) -> AdapterResponse:
        """Get current rate limit status for Alpha Vantage."""
        # Alpha Vantage doesn't provide real-time rate limit status
        # We return the configured limits
        return AdapterResponse.success_response(
            data={
                "requests_remaining": None,  # Unknown without tracking
                "reset_time": None,  # Resets every minute
                "quota_used_percent": 0.0,  # Would need to track usage
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "rate_limit_per_day": self.rate_limit_per_day,
                "provider_info": "Alpha Vantage limits: 5 requests/minute, 500 requests/day (free tier)"
            },
            response_time_ms=0.0
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for Alpha Vantage adapter."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Alpha Vantage API key (required)",
                    "minLength": 1
                },
                "base_url": {
                    "type": "string",
                    "description": "Base URL for Alpha Vantage API",
                    "default": "https://www.alphavantage.co/query"
                },
                "timeout": {
                    "type": "number",
                    "description": "Request timeout in seconds",
                    "default": 30
                },
                "rate_limit_per_minute": {
                    "type": "number",
                    "description": "Rate limit per minute",
                    "default": 5
                },
                "rate_limit_per_day": {
                    "type": "number",
                    "description": "Rate limit per day",
                    "default": 500
                }
            },
            "required": ["api_key"]
        }

    def get_example_configuration(self) -> Dict[str, Any]:
        """Return example configuration for Alpha Vantage adapter."""
        return {
            "api_key": "YOUR_API_KEY_HERE",
            "base_url": "https://www.alphavantage.co/query",
            "timeout": 30,
            "rate_limit_per_minute": 5,
            "rate_limit_per_day": 500
        }

    async def cleanup(self) -> None:
        """Clean up Alpha Vantage adapter resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        await super().cleanup()
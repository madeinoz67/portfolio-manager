"""
Alpha Vantage market data provider adapter.

Implements the MarketDataAdapter interface for Alpha Vantage API,
providing real-time and historical stock market data with comprehensive
error handling, rate limiting, and metrics collection.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime
import logging

from ..base_adapter import (
    MarketDataAdapter,
    AdapterResponse,
    ProviderCapabilities,
    CostInformation,
    AdapterError,
    RateLimitError,
    AuthenticationError,
    InvalidSymbolError,
    ProviderTimeoutError
)
from ..mixins import ResilientProviderMixin, MetricsCollectionMixin, CachingMixin

logger = logging.getLogger(__name__)


class AlphaVantageAdapter(ResilientProviderMixin, MetricsCollectionMixin, CachingMixin, MarketDataAdapter):
    """
    Alpha Vantage API adapter for market data.

    Provides access to Alpha Vantage's comprehensive market data API
    with built-in resilience, metrics collection, and caching.
    """

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize Alpha Vantage adapter.

        Args:
            provider_name: Unique identifier for this provider instance
            config: Configuration containing api_key, base_url, etc.
        """
        super().__init__(provider_name, config)

        # Alpha Vantage specific configuration
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://www.alphavantage.co/query")
        self.timeout = config.get("timeout", 30)

        # Rate limiting (Alpha Vantage free tier: 5 calls/min, 500 calls/day)
        self.calls_per_minute = config.get("calls_per_minute", 5)
        self.calls_per_day = config.get("calls_per_day", 500)

        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Alpha Vantage capabilities."""
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk_quotes=False,  # Alpha Vantage doesn't support bulk quotes
            max_symbols_per_request=1,
            rate_limit_per_minute=self.calls_per_minute,
            rate_limit_per_day=self.calls_per_day,
            supports_intraday=True,
            supports_options=False,
            supports_crypto=True
        )

    @property
    def cost_info(self) -> CostInformation:
        """Return Alpha Vantage cost information."""
        # Free tier: 5 calls/min, 500 calls/day
        # Premium starts at $49.99/month for 1200 calls/min
        cost_per_call = None
        cost_model = "freemium"

        if self.calls_per_minute > 5:
            # Estimate cost for premium tier
            cost_per_call = Decimal("0.042")  # Rough estimate: $49.99/1200 calls
            cost_model = "subscription"

        return CostInformation(
            cost_per_call=cost_per_call,
            cost_model=cost_model,
            monthly_quota=self.calls_per_day * 30,
            burst_quota=self.calls_per_minute,
            overage_cost=None  # Alpha Vantage uses hard limits, not overage
        )

    async def initialize(self) -> bool:
        """Initialize the Alpha Vantage adapter."""
        if not self.api_key:
            self.logger.error("Alpha Vantage API key not provided")
            return False

        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)

        # Test API key with a simple call
        try:
            test_response = await self._make_api_call("GLOBAL_QUOTE", {"symbol": "AAPL"})
            if "Error Message" in test_response or "Invalid API call" in str(test_response):
                self.logger.error("Alpha Vantage API key validation failed")
                return False

            self.logger.info(f"Alpha Vantage adapter initialized successfully for {self.provider_name}")
            return True

        except Exception as e:
            self.logger.error(f"Alpha Vantage initialization failed: {e}")
            return False

    async def health_check(self) -> AdapterResponse:
        """Perform health check by fetching a quote for AAPL."""
        return await self._execute_with_resilience(
            self._health_check_impl,
            operation_name="health_check",
            timeout_seconds=10
        )

    async def _health_check_impl(self) -> AdapterResponse:
        """Implementation of health check."""
        try:
            data = await self._make_api_call("GLOBAL_QUOTE", {"symbol": "AAPL"})

            if "Error Message" in data:
                return AdapterResponse.error_response(
                    error_message=f"Alpha Vantage error: {data['Error Message']}",
                    error_code="API_ERROR"
                )

            if "Global Quote" not in data:
                return AdapterResponse.error_response(
                    error_message="Unexpected response format from Alpha Vantage",
                    error_code="INVALID_RESPONSE"
                )

            return AdapterResponse.success_response(
                data={"status": "healthy", "test_symbol": "AAPL"},
                response_time_ms=0.0  # Will be set by resilience layer
            )

        except Exception as e:
            return AdapterResponse.error_response(
                error_message=f"Health check failed: {str(e)}",
                error_code="HEALTH_CHECK_FAILED"
            )

    async def fetch_prices(self, symbols: Union[str, List[str]]) -> AdapterResponse:
        """
        Unified interface for fetching prices.

        Alpha Vantage doesn't support bulk quotes, so this implementation
        always uses sequential single API calls regardless of input type.
        """
        # Normalize input to list for processing
        if isinstance(symbols, str):
            symbol_list = [symbols]
            return_single = True
        else:
            symbol_list = symbols
            return_single = False

        # Alpha Vantage optimization: Always use single API calls
        # This provider doesn't support bulk, so we use sequential calls
        if len(symbol_list) == 1:
            # Single symbol - use caching and full resilience
            cache_key = self._cache_key("current_price", symbol_list[0])
            response = await self._execute_with_cache(
                self._execute_with_resilience,
                cache_key,
                self._get_current_price_impl,
                symbol_list[0],
                operation_name=f"fetch_prices:single:{symbol_list[0]}",
                timeout_seconds=self.timeout
            )

            if return_single:
                return response
            else:
                # Wrap single result in dict format for list input
                if response.success:
                    return AdapterResponse.success_response(
                        data={symbol_list[0]: response.data},
                        response_time_ms=response.response_time_ms
                    )
                else:
                    return AdapterResponse.success_response(
                        data={symbol_list[0]: None},
                        response_time_ms=response.response_time_ms
                    )
        else:
            # Multiple symbols - sequential calls
            response = await self._execute_with_resilience(
                self._get_multiple_prices_impl,
                symbol_list,
                operation_name=f"fetch_prices:multiple:{len(symbol_list)}",
                timeout_seconds=self.timeout * len(symbol_list)
            )
            return response

    async def get_current_price(self, symbol: str) -> AdapterResponse:
        """Legacy method - delegates to fetch_prices."""
        return await self.fetch_prices(symbol)

    async def _get_current_price_impl(self, symbol: str) -> AdapterResponse:
        """Implementation of get_current_price."""
        try:
            data = await self._make_api_call("GLOBAL_QUOTE", {"symbol": symbol})

            if "Error Message" in data:
                if "Invalid API call" in data["Error Message"]:
                    raise InvalidSymbolError(f"Invalid symbol: {symbol}", self.provider_name)
                else:
                    raise AdapterError(f"Alpha Vantage error: {data['Error Message']}", self.provider_name)

            if "Note" in data:
                # Rate limit message
                raise RateLimitError("Alpha Vantage rate limit reached", self.provider_name)

            if "Global Quote" not in data:
                raise AdapterError("Unexpected response format", self.provider_name)

            quote = data["Global Quote"]

            # Parse Alpha Vantage response
            current_price = Decimal(quote.get("05. price", "0"))
            previous_close = Decimal(quote.get("08. previous close", "0"))
            volume = int(quote.get("06. volume", "0"))

            # Calculate market cap estimate (not provided by Alpha Vantage directly)
            market_cap = None

            price_data = {
                "symbol": symbol,
                "current_price": current_price,
                "previous_close": previous_close,
                "currency": "USD",  # Alpha Vantage primarily uses USD
                "last_updated": datetime.utcnow(),
                "volume": volume,
                "market_cap": market_cap,
                "daily_change": current_price - previous_close,
                "daily_change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                "provider": self.provider_name
            }

            return AdapterResponse.success_response(
                data=price_data,
                response_time_ms=0.0  # Will be set by resilience layer
            )

        except (RateLimitError, InvalidSymbolError, AdapterError):
            raise
        except Exception as e:
            raise AdapterError(f"Unexpected error getting price for {symbol}: {str(e)}", self.provider_name)

    async def get_multiple_prices(self, symbols: List[str]) -> AdapterResponse:
        """Legacy method - delegates to fetch_prices."""
        return await self.fetch_prices(symbols)

    async def _get_multiple_prices_impl(self, symbols: List[str]) -> AdapterResponse:
        """Implementation of get_multiple_prices."""
        results = {}
        errors = {}

        # Alpha Vantage doesn't support bulk quotes, so we need sequential calls
        for symbol in symbols:
            try:
                response = await self.get_current_price(symbol)
                if response.success:
                    results[symbol] = response.data
                else:
                    errors[symbol] = response.error_message

                # Small delay to respect rate limits
                await asyncio.sleep(0.2)

            except Exception as e:
                errors[symbol] = str(e)

        return AdapterResponse.success_response(
            data={
                "results": results,
                "errors": errors,
                "total_requested": len(symbols),
                "successful": len(results),
                "failed": len(errors)
            },
            response_time_ms=0.0  # Will be set by resilience layer
        )

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> AdapterResponse:
        """Get historical data from Alpha Vantage."""
        return await self._execute_with_resilience(
            self._get_historical_data_impl,
            symbol,
            start_date,
            end_date,
            interval,
            operation_name=f"get_historical_data:{symbol}",
            timeout_seconds=self.timeout
        )

    async def _get_historical_data_impl(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> AdapterResponse:
        """Implementation of get_historical_data."""
        try:
            # Map interval to Alpha Vantage function
            if interval == "1d":
                function = "TIME_SERIES_DAILY"
                params = {"symbol": symbol, "outputsize": "full"}
            elif interval == "1h":
                function = "TIME_SERIES_INTRADAY"
                params = {"symbol": symbol, "interval": "60min", "outputsize": "full"}
            else:
                raise AdapterError(f"Unsupported interval: {interval}", self.provider_name)

            data = await self._make_api_call(function, params)

            if "Error Message" in data:
                raise AdapterError(f"Alpha Vantage error: {data['Error Message']}", self.provider_name)

            if "Note" in data:
                raise RateLimitError("Alpha Vantage rate limit reached", self.provider_name)

            # Parse time series data
            time_series_key = list(data.keys())[1]  # Skip metadata
            time_series = data[time_series_key]

            historical_data = []
            for date_str, values in time_series.items():
                date_obj = datetime.fromisoformat(date_str.replace(" ", "T"))

                # Filter by date range
                if start_date <= date_obj <= end_date:
                    historical_data.append({
                        "date": date_obj,
                        "open": Decimal(values["1. open"]),
                        "high": Decimal(values["2. high"]),
                        "low": Decimal(values["3. low"]),
                        "close": Decimal(values["4. close"]),
                        "volume": int(values["5. volume"])
                    })

            historical_data.sort(key=lambda x: x["date"])

            return AdapterResponse.success_response(
                data={
                    "symbol": symbol,
                    "interval": interval,
                    "start_date": start_date,
                    "end_date": end_date,
                    "data": historical_data
                },
                response_time_ms=0.0
            )

        except (RateLimitError, AdapterError):
            raise
        except Exception as e:
            raise AdapterError(f"Error getting historical data for {symbol}: {str(e)}", self.provider_name)

    async def validate_symbols(self, symbols: List[str]) -> AdapterResponse:
        """Validate symbols by attempting to fetch quotes."""
        valid_symbols = []
        invalid_symbols = []

        for symbol in symbols[:5]:  # Limit validation to avoid rate limits
            try:
                response = await self.get_current_price(symbol)
                if response.success:
                    valid_symbols.append(symbol)
                else:
                    invalid_symbols.append(symbol)
            except InvalidSymbolError:
                invalid_symbols.append(symbol)
            except Exception:
                # If we can't determine, assume invalid to be safe
                invalid_symbols.append(symbol)

        return AdapterResponse.success_response(
            data={
                "valid_symbols": valid_symbols,
                "invalid_symbols": invalid_symbols,
                "total_checked": len(valid_symbols) + len(invalid_symbols)
            },
            response_time_ms=0.0
        )

    async def get_rate_limit_status(self) -> AdapterResponse:
        """Get current rate limit status."""
        # Alpha Vantage doesn't provide rate limit headers, so we estimate
        metrics = self.get_metrics_summary()

        return AdapterResponse.success_response(
            data={
                "requests_remaining": max(0, self.calls_per_minute - len(self._request_times)),
                "reset_time": None,  # Alpha Vantage uses rolling windows
                "quota_used_percent": (len(self._request_times) / self.calls_per_minute) * 100,
                "total_requests": metrics["total_requests"]
            },
            response_time_ms=0.0
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for Alpha Vantage."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Alpha Vantage API key",
                    "minLength": 8
                },
                "base_url": {
                    "type": "string",
                    "description": "Base URL for API requests",
                    "default": "https://www.alphavantage.co/query"
                },
                "timeout": {
                    "type": "number",
                    "description": "Request timeout in seconds",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 120
                },
                "calls_per_minute": {
                    "type": "number",
                    "description": "Rate limit calls per minute",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 1200
                },
                "calls_per_day": {
                    "type": "number",
                    "description": "Rate limit calls per day",
                    "default": 500,
                    "minimum": 25,
                    "maximum": 100000
                }
            },
            "required": ["api_key"]
        }

    def get_example_configuration(self) -> Dict[str, Any]:
        """Return example configuration for Alpha Vantage."""
        return {
            "api_key": "YOUR_ALPHA_VANTAGE_API_KEY",
            "base_url": "https://www.alphavantage.co/query",
            "timeout": 30,
            "calls_per_minute": 5,
            "calls_per_day": 500
        }

    async def _make_api_call(self, function: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API call to Alpha Vantage."""
        if not self._session:
            raise AdapterError("Adapter not initialized", self.provider_name)

        # Build URL parameters
        url_params = {
            "function": function,
            "apikey": self.api_key,
            **params
        }

        try:
            async with self._session.get(self.base_url, params=url_params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded", self.provider_name)
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key", self.provider_name)
                else:
                    raise AdapterError(f"HTTP {response.status}: {response.reason}", self.provider_name)

        except aiohttp.ClientTimeout:
            raise ProviderTimeoutError(f"Request timeout after {self.timeout}s", self.provider_name)
        except aiohttp.ClientError as e:
            raise AdapterError(f"Network error: {str(e)}", self.provider_name)

    async def cleanup(self) -> None:
        """Clean up resources."""
        await super().cleanup()
        if self._session:
            await self._session.close()
            self._session = None
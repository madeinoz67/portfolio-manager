"""
Yahoo Finance market data provider adapter.

Implements the MarketDataAdapter interface for Yahoo Finance API,
providing real-time and historical stock market data with comprehensive
error handling, rate limiting, and metrics collection.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import json

from ..base_adapter import (
    MarketDataAdapter,
    AdapterResponse,
    ProviderCapabilities,
    CostInformation,
    AdapterError,
    RateLimitError,
    InvalidSymbolError,
    ProviderTimeoutError
)
from ..mixins import ResilientProviderMixin, MetricsCollectionMixin, CachingMixin

logger = logging.getLogger(__name__)


class YahooFinanceAdapter(ResilientProviderMixin, MetricsCollectionMixin, CachingMixin, MarketDataAdapter):
    """
    Yahoo Finance API adapter for market data.

    Provides access to Yahoo Finance's market data API with built-in
    resilience, metrics collection, and caching. Uses the unofficial
    Yahoo Finance API endpoints.
    """

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize Yahoo Finance adapter.

        Args:
            provider_name: Unique identifier for this provider instance
            config: Configuration containing base_url, timeout, etc.
        """
        super().__init__(provider_name, config)

        # Yahoo Finance specific configuration
        self.base_url = config.get("base_url", "https://query1.finance.yahoo.com")
        self.timeout = config.get("timeout", 30)

        # Rate limiting (conservative limits for unofficial API)
        self.calls_per_minute = config.get("calls_per_minute", 60)
        self.calls_per_day = config.get("calls_per_day", 2000)

        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Yahoo Finance capabilities."""
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk_quotes=True,  # Yahoo Finance supports bulk quotes
            max_symbols_per_request=100,
            rate_limit_per_minute=self.calls_per_minute,
            rate_limit_per_day=self.calls_per_day,
            supports_intraday=True,
            supports_options=False,
            supports_crypto=True
        )

    @property
    def cost_info(self) -> CostInformation:
        """Return Yahoo Finance cost information."""
        return CostInformation(
            cost_per_call=Decimal("0.0"),  # Free service
            cost_model="free",
            monthly_quota=self.calls_per_day * 30,
            burst_quota=self.calls_per_minute,
            overage_cost=None
        )

    async def initialize(self) -> bool:
        """Initialize the Yahoo Finance adapter."""
        # Create HTTP session with realistic headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)

        # Test with a simple quote request
        try:
            test_response = await self._make_quote_request(["AAPL"])
            if not test_response or "error" in test_response:
                self.logger.error("Yahoo Finance API test failed")
                return False

            self.logger.info(f"Yahoo Finance adapter initialized successfully for {self.provider_name}")
            return True

        except Exception as e:
            self.logger.error(f"Yahoo Finance initialization failed: {e}")
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
            data = await self._make_quote_request(["AAPL"])

            if not data or "error" in data:
                return AdapterResponse.error_response(
                    error_message="Yahoo Finance API health check failed",
                    error_code="API_ERROR"
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

    async def get_current_price(self, symbol: str) -> AdapterResponse:
        """Get current price for a single symbol."""
        cache_key = self._cache_key("current_price", symbol)
        return await self._execute_with_cache(
            self._execute_with_resilience,
            cache_key,
            self._get_current_price_impl,
            symbol,
            operation_name=f"get_current_price:{symbol}",
            timeout_seconds=self.timeout
        )

    async def _get_current_price_impl(self, symbol: str) -> AdapterResponse:
        """Implementation of get_current_price."""
        try:
            data = await self._make_quote_request([symbol])

            if not data or "error" in data:
                raise AdapterError(f"Yahoo Finance error for {symbol}", self.provider_name)

            quote_response = data.get("quoteResponse", {})
            results = quote_response.get("result", [])

            if not results:
                raise InvalidSymbolError(f"No data returned for symbol: {symbol}", self.provider_name)

            quote = results[0]

            # Check if symbol was found
            if quote.get("quoteType") == "NONE" or not quote.get("regularMarketPrice"):
                raise InvalidSymbolError(f"Invalid or inactive symbol: {symbol}", self.provider_name)

            # Parse Yahoo Finance response
            current_price = Decimal(str(quote.get("regularMarketPrice", 0)))
            previous_close = Decimal(str(quote.get("regularMarketPreviousClose", 0)))
            volume = quote.get("regularMarketVolume", 0)
            market_cap = quote.get("marketCap")

            if market_cap:
                market_cap = Decimal(str(market_cap))

            # Get company name
            company_name = quote.get("longName") or quote.get("shortName") or symbol

            price_data = {
                "symbol": symbol,
                "current_price": current_price,
                "previous_close": previous_close,
                "currency": quote.get("currency", "USD"),
                "last_updated": datetime.utcnow(),
                "volume": volume,
                "market_cap": market_cap,
                "company_name": company_name,
                "daily_change": current_price - previous_close,
                "daily_change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                "provider": self.provider_name,
                "high_52_week": Decimal(str(quote.get("fiftyTwoWeekHigh", 0))) if quote.get("fiftyTwoWeekHigh") else None,
                "low_52_week": Decimal(str(quote.get("fiftyTwoWeekLow", 0))) if quote.get("fiftyTwoWeekLow") else None,
                "dividend_yield": Decimal(str(quote.get("dividendYield", 0))) if quote.get("dividendYield") else None,
                "pe_ratio": Decimal(str(quote.get("trailingPE", 0))) if quote.get("trailingPE") else None
            }

            return AdapterResponse.success_response(
                data=price_data,
                response_time_ms=0.0  # Will be set by resilience layer
            )

        except (InvalidSymbolError, AdapterError):
            raise
        except Exception as e:
            raise AdapterError(f"Unexpected error getting price for {symbol}: {str(e)}", self.provider_name)

    async def get_multiple_prices(self, symbols: List[str]) -> AdapterResponse:
        """Get current prices for multiple symbols (bulk request)."""
        return await self._execute_with_resilience(
            self._get_multiple_prices_impl,
            symbols,
            operation_name=f"get_multiple_prices:{len(symbols)}",
            timeout_seconds=self.timeout
        )

    async def _get_multiple_prices_impl(self, symbols: List[str]) -> AdapterResponse:
        """Implementation of get_multiple_prices using bulk request."""
        try:
            # Yahoo Finance supports bulk quotes, process in batches
            batch_size = min(self.capabilities.max_symbols_per_request, 50)
            all_results = {}
            all_errors = {}

            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]

                try:
                    data = await self._make_quote_request(batch_symbols)

                    if not data or "error" in data:
                        # If batch fails, add all symbols to errors
                        for symbol in batch_symbols:
                            all_errors[symbol] = "Batch request failed"
                        continue

                    quote_response = data.get("quoteResponse", {})
                    results = quote_response.get("result", [])

                    # Process each result
                    processed_symbols = set()
                    for quote in results:
                        symbol = quote.get("symbol")
                        if not symbol:
                            continue

                        processed_symbols.add(symbol)

                        try:
                            # Use same parsing logic as single quote
                            if quote.get("quoteType") == "NONE" or not quote.get("regularMarketPrice"):
                                all_errors[symbol] = "Invalid or inactive symbol"
                                continue

                            current_price = Decimal(str(quote.get("regularMarketPrice", 0)))
                            previous_close = Decimal(str(quote.get("regularMarketPreviousClose", 0)))
                            volume = quote.get("regularMarketVolume", 0)
                            market_cap = quote.get("marketCap")

                            if market_cap:
                                market_cap = Decimal(str(market_cap))

                            all_results[symbol] = {
                                "symbol": symbol,
                                "current_price": current_price,
                                "previous_close": previous_close,
                                "currency": quote.get("currency", "USD"),
                                "last_updated": datetime.utcnow(),
                                "volume": volume,
                                "market_cap": market_cap,
                                "company_name": quote.get("longName") or quote.get("shortName") or symbol,
                                "daily_change": current_price - previous_close,
                                "daily_change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                                "provider": self.provider_name
                            }

                        except Exception as e:
                            all_errors[symbol] = f"Error parsing data: {str(e)}"

                    # Add symbols that weren't in the response to errors
                    for symbol in batch_symbols:
                        if symbol not in processed_symbols and symbol not in all_errors:
                            all_errors[symbol] = "Symbol not found in response"

                    # Small delay between batches
                    if i + batch_size < len(symbols):
                        await asyncio.sleep(0.1)

                except Exception as e:
                    # If batch fails, add all symbols to errors
                    for symbol in batch_symbols:
                        all_errors[symbol] = f"Batch error: {str(e)}"

            return AdapterResponse.success_response(
                data={
                    "results": all_results,
                    "errors": all_errors,
                    "total_requested": len(symbols),
                    "successful": len(all_results),
                    "failed": len(all_errors)
                },
                response_time_ms=0.0  # Will be set by resilience layer
            )

        except Exception as e:
            raise AdapterError(f"Error getting multiple prices: {str(e)}", self.provider_name)

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> AdapterResponse:
        """Get historical data from Yahoo Finance."""
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
            # Convert interval to Yahoo Finance format
            interval_map = {
                "1m": "1m", "2m": "2m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "1d": "1d", "5d": "5d", "1wk": "1wk", "1mo": "1mo", "3mo": "3mo"
            }

            yahoo_interval = interval_map.get(interval, "1d")

            # Convert dates to timestamps
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())

            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                "period1": start_timestamp,
                "period2": end_timestamp,
                "interval": yahoo_interval,
                "includePrePost": "false",
                "events": "div,splits"
            }

            data = await self._make_api_request(url, params)

            if not data or "error" in data:
                raise AdapterError(f"Yahoo Finance historical data error for {symbol}", self.provider_name)

            chart = data.get("chart", {})
            results = chart.get("result", [])

            if not results:
                raise InvalidSymbolError(f"No historical data for symbol: {symbol}", self.provider_name)

            result = results[0]
            meta = result.get("meta", {})
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {})
            quotes = indicators.get("quote", [{}])[0]

            # Parse historical data
            historical_data = []
            opens = quotes.get("open", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])
            closes = quotes.get("close", [])
            volumes = quotes.get("volume", [])

            for i, timestamp in enumerate(timestamps):
                if i < len(closes) and closes[i] is not None:
                    historical_data.append({
                        "date": datetime.fromtimestamp(timestamp),
                        "open": Decimal(str(opens[i])) if i < len(opens) and opens[i] is not None else None,
                        "high": Decimal(str(highs[i])) if i < len(highs) and highs[i] is not None else None,
                        "low": Decimal(str(lows[i])) if i < len(lows) and lows[i] is not None else None,
                        "close": Decimal(str(closes[i])),
                        "volume": volumes[i] if i < len(volumes) and volumes[i] is not None else 0
                    })

            return AdapterResponse.success_response(
                data={
                    "symbol": symbol,
                    "interval": interval,
                    "start_date": start_date,
                    "end_date": end_date,
                    "currency": meta.get("currency", "USD"),
                    "data": historical_data
                },
                response_time_ms=0.0
            )

        except (InvalidSymbolError, AdapterError):
            raise
        except Exception as e:
            raise AdapterError(f"Error getting historical data for {symbol}: {str(e)}", self.provider_name)

    async def validate_symbols(self, symbols: List[str]) -> AdapterResponse:
        """Validate symbols by attempting to fetch quotes."""
        try:
            # Use bulk quote to validate efficiently
            response = await self.get_multiple_prices(symbols)

            if response.success:
                data = response.data
                valid_symbols = list(data["results"].keys())
                invalid_symbols = list(data["errors"].keys())
            else:
                # Fallback to individual validation
                valid_symbols = []
                invalid_symbols = []

                for symbol in symbols[:10]:  # Limit to avoid rate limits
                    try:
                        quote_response = await self.get_current_price(symbol)
                        if quote_response.success:
                            valid_symbols.append(symbol)
                        else:
                            invalid_symbols.append(symbol)
                    except Exception:
                        invalid_symbols.append(symbol)

            return AdapterResponse.success_response(
                data={
                    "valid_symbols": valid_symbols,
                    "invalid_symbols": invalid_symbols,
                    "total_checked": len(valid_symbols) + len(invalid_symbols)
                },
                response_time_ms=0.0
            )

        except Exception as e:
            raise AdapterError(f"Error validating symbols: {str(e)}", self.provider_name)

    async def get_rate_limit_status(self) -> AdapterResponse:
        """Get current rate limit status."""
        # Yahoo Finance doesn't provide rate limit headers, so we estimate
        metrics = self.get_metrics_summary()

        return AdapterResponse.success_response(
            data={
                "requests_remaining": max(0, self.calls_per_minute - len(self._request_times)),
                "reset_time": None,  # Rolling window
                "quota_used_percent": (len(self._request_times) / self.calls_per_minute) * 100,
                "total_requests": metrics["total_requests"]
            },
            response_time_ms=0.0
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Return configuration schema for Yahoo Finance."""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL for API requests",
                    "default": "https://query1.finance.yahoo.com"
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
                    "default": 60,
                    "minimum": 1,
                    "maximum": 300
                },
                "calls_per_day": {
                    "type": "number",
                    "description": "Rate limit calls per day",
                    "default": 2000,
                    "minimum": 100,
                    "maximum": 50000
                }
            },
            "required": []
        }

    def get_example_configuration(self) -> Dict[str, Any]:
        """Return example configuration for Yahoo Finance."""
        return {
            "base_url": "https://query1.finance.yahoo.com",
            "timeout": 30,
            "calls_per_minute": 60,
            "calls_per_day": 2000
        }

    async def _make_quote_request(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """Make a quote request to Yahoo Finance."""
        symbols_str = ",".join(symbols)
        url = f"{self.base_url}/v7/finance/quote"
        params = {"symbols": symbols_str}

        return await self._make_api_request(url, params)

    async def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make an API request to Yahoo Finance."""
        if not self._session:
            raise AdapterError("Adapter not initialized", self.provider_name)

        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded", self.provider_name)
                elif response.status == 404:
                    raise InvalidSymbolError("Symbol not found", self.provider_name)
                else:
                    raise AdapterError(f"HTTP {response.status}: {response.reason}", self.provider_name)

        except aiohttp.ClientTimeout:
            raise ProviderTimeoutError(f"Request timeout after {self.timeout}s", self.provider_name)
        except aiohttp.ClientError as e:
            raise AdapterError(f"Network error: {str(e)}", self.provider_name)
        except json.JSONDecodeError as e:
            raise AdapterError(f"Invalid JSON response: {str(e)}", self.provider_name)

    async def cleanup(self) -> None:
        """Clean up resources."""
        await super().cleanup()
        if self._session:
            await self._session.close()
            self._session = None
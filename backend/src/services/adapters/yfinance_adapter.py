"""
Yahoo Finance adapter implementation.

Provides market data through the Yahoo Finance API with full metrics tracking.
"""

import asyncio
import aiohttp
import time
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

        # Yahoo Finance doesn't require API key but has rate limits
        self.rate_limit_per_minute = config.get("rate_limit_per_minute", 100)
        self.rate_limit_per_day = config.get("rate_limit_per_day", 10000)

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Return Yahoo Finance capabilities."""
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk_quotes=True,
            max_symbols_per_request=50,  # Yahoo supports bulk requests
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
            # Test connectivity with a simple request
            test_response = await self.health_check()
            return test_response.success
        except Exception as e:
            self.logger.error(f"Failed to initialize Yahoo Finance adapter: {e}")
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
        """Fetch data for a single symbol."""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

        url = f"{self.base_url}/{symbol}"

        try:
            async with self._session.get(url) as response:
                if response.status == 429:
                    raise RateLimitError("Yahoo Finance rate limit exceeded", self.provider_name, "RATE_LIMIT")

                if response.status != 200:
                    raise AdapterError(f"HTTP {response.status}", self.provider_name, str(response.status))

                data = await response.json()
                return self._parse_yahoo_response(symbol, data)

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"Timeout fetching {symbol}", self.provider_name, "TIMEOUT")

    async def _fetch_multiple_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch data for multiple symbols using Yahoo's bulk API."""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

        # Yahoo Finance bulk request - join symbols with commas
        symbols_param = ','.join(symbols)
        url = f"{self.base_url}/{symbols_param}"

        try:
            async with self._session.get(url) as response:
                if response.status == 429:
                    raise RateLimitError("Yahoo Finance rate limit exceeded", self.provider_name, "RATE_LIMIT")

                if response.status != 200:
                    raise AdapterError(f"HTTP {response.status}", self.provider_name, str(response.status))

                data = await response.json()
                return self._parse_yahoo_bulk_response(symbols, data)

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"Timeout fetching bulk symbols", self.provider_name, "TIMEOUT")

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
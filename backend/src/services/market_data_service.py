"""
Market data service for fetching and managing stock price data.

Provides abstraction layer for different market data providers
with fallback support and caching.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import asyncio
import aiohttp
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from src.models.market_data_provider import MarketDataProvider
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.api_usage_metrics import ApiUsageMetrics
from src.utils.datetime_utils import utc_now
from src.services.activity_service import log_provider_activity
from src.core.logging import get_logger
from src.utils.datetime_utils import to_iso_string

logger = get_logger(__name__)


class MarketDataService:
    """Service for fetching and managing market data."""

    def __init__(self, db: Session):
        self.db = db
        self._session: Optional[aiohttp.ClientSession] = None
        self._recent_fetches = {}  # Track recent fetches to avoid duplicates

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Portfolio-Manager/1.0"}
            )
        return self._session

    async def close_session(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def get_enabled_providers(self) -> List[MarketDataProvider]:
        """Get list of enabled providers ordered by priority."""
        return self.db.query(MarketDataProvider).filter(
            MarketDataProvider.is_enabled == True
        ).order_by(MarketDataProvider.priority).all()

    def supports_bulk_operations(self, provider) -> bool:
        """Check if a provider supports bulk operations."""
        if not provider.is_enabled:
            return False

        # Currently supported bulk providers
        if provider.name == "yfinance":
            return True  # yfinance supports unlimited bulk operations
        elif provider.name == "alpha_vantage":
            return provider.api_key is not None  # Alpha Vantage needs API key for bulk
        else:
            return False  # Other providers don't support bulk yet

    def has_bulk_capable_providers(self) -> bool:
        """Check if any enabled providers support bulk operations."""
        providers = self.get_enabled_providers()
        return any(self.supports_bulk_operations(provider) for provider in providers)

    async def fetch_price(self, symbol: str) -> Optional[Dict]:
        """Fetch current price for a symbol using available providers."""
        # Check if we've fetched this symbol recently (within 10 minutes)
        now = datetime.utcnow()
        if symbol in self._recent_fetches:
            last_fetch_time = self._recent_fetches[symbol]
            if (now - last_fetch_time).total_seconds() < 600:  # 10 minutes
                logger.info(f"Skipping {symbol} - fetched recently at {last_fetch_time}")
                return None

        providers = self.get_enabled_providers()

        for provider in providers:
            try:
                start_time = datetime.utcnow()
                price_data = await self._fetch_from_provider_single(symbol, provider)
                end_time = datetime.utcnow()

                if price_data:
                    # Record successful fetch time
                    self._recent_fetches[symbol] = now

                    # Store in database
                    await self._store_price_data(symbol, price_data, provider)

                    # Log successful API usage
                    self._log_api_usage(provider, symbol, 200, True)

                    # Log successful activity for admin dashboard
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    log_provider_activity(
                        db_session=self.db,
                        provider_id=provider.name,
                        activity_type="API_CALL",
                        description=f"Successfully fetched price for {symbol}: ${price_data['price']}",
                        status="success",
                        metadata={
                            "symbol": symbol,
                            "price": str(price_data["price"]),
                            "volume": price_data.get("volume"),
                            "response_time_ms": response_time_ms,
                            "provider_display_name": provider.display_name
                        }
                    )

                    return price_data

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {provider.name}: {e}")
                # Log failed API usage
                self._log_api_usage(provider, symbol, 500, False, str(e))

                # Log error activity for admin dashboard
                log_provider_activity(
                    db_session=self.db,
                    provider_id=provider.name,
                    activity_type="API_ERROR",
                    description=f"Failed to fetch {symbol} price: {str(e)[:100]}",
                    status="error",
                    metadata={
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "provider_display_name": provider.display_name
                    }
                )
                continue

        logger.error(f"Failed to fetch price for {symbol} from all providers")
        # Log that all providers failed
        if providers:
            log_provider_activity(
                db_session=self.db,
                provider_id="system",
                activity_type="PROVIDER_FAILURE",
                description=f"All providers failed for symbol {symbol}",
                status="error",
                metadata={
                    "symbol": symbol,
                    "providers_tried": [p.name for p in providers],
                    "total_providers": len(providers)
                }
            )

        return None

    async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch prices for multiple symbols using bulk operations when possible."""
        start_time = datetime.utcnow()

        # Group symbols by provider priority and use bulk operations
        price_data = {}
        success_count = 0
        error_count = 0

        providers = self.get_enabled_providers()
        remaining_symbols = symbols.copy()

        for provider in providers:
            if not remaining_symbols:
                break

            try:
                # Try bulk fetch for this provider
                if (provider.name == "yfinance" and len(remaining_symbols) > 1) or \
                   (provider.name == "alpha_vantage" and len(remaining_symbols) > 1 and provider.api_key):

                    # Determine which bulk method to use
                    if provider.name == "yfinance":
                        logger.info(f"Using bulk yfinance fetch for {len(remaining_symbols)} symbols")
                        bulk_results = await self._bulk_fetch_from_yfinance(remaining_symbols)
                    elif provider.name == "alpha_vantage":
                        logger.info(f"Using bulk Alpha Vantage fetch for {len(remaining_symbols)} symbols")
                        bulk_results = await self._bulk_fetch_from_alpha_vantage(remaining_symbols, provider.api_key)

                    successful_symbols = []

                    for symbol, result in bulk_results.items():
                        if result:
                            price_data[symbol] = result
                            success_count += 1
                            successful_symbols.append(symbol)
                            # Store in database
                            await self._store_price_data(symbol, result, provider)
                            # Log API usage
                            self._log_api_usage(provider, symbol, 200, True)

                    # Remove successfully fetched symbols from remaining
                    remaining_symbols = [s for s in remaining_symbols if s not in successful_symbols]

                    # Log bulk activity
                    if successful_symbols:
                        log_provider_activity(
                            db_session=self.db,
                            provider_id=provider.name,
                            activity_type="BULK_PRICE_UPDATE",
                            description=f"Bulk fetch from {provider.name}: {len(successful_symbols)} symbols updated",
                            status="success",
                            metadata={
                                "symbols_fetched": successful_symbols,
                                "bulk_operation": True,
                                "provider": provider.name,
                                "efficiency_gain": f"{len(successful_symbols)}x fewer API calls"
                            }
                        )
                else:
                    # Fall back to individual fetches for this provider
                    logger.info(f"Using individual fetch for {len(remaining_symbols)} symbols with {provider.name}")
                    tasks = [self._fetch_single_with_provider(symbol, provider) for symbol in remaining_symbols]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    successful_symbols = []
                    for symbol, result in zip(remaining_symbols, results):
                        if isinstance(result, dict) and result:
                            price_data[symbol] = result
                            success_count += 1
                            successful_symbols.append(symbol)
                        elif isinstance(result, Exception):
                            logger.error(f"Error fetching {symbol}: {result}")
                            error_count += 1

                    # Remove successfully fetched symbols from remaining
                    remaining_symbols = [s for s in remaining_symbols if s not in successful_symbols]

            except Exception as e:
                logger.error(f"Error with bulk fetch from {provider.name}: {e}")
                error_count += len(remaining_symbols)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Log overall bulk operation activity
        logger.info(f"Bulk fetch completed: {success_count}/{len(symbols)} successful in {duration:.2f}s")

        if success_count > 0:
            log_provider_activity(
                db_session=self.db,
                provider_id="system",
                activity_type="BULK_PRICE_UPDATE",
                description=f"Optimized bulk price update completed for {success_count}/{len(symbols)} symbols",
                status="success" if error_count == 0 else "warning",
                metadata={
                    "total_symbols": len(symbols),
                    "successful": success_count,
                    "failed": error_count,
                    "duration_seconds": round(duration, 2),
                    "success_rate": round(success_count / len(symbols), 2),
                    "bulk_optimization": "enabled",
                    "performance_improvement": "Up to Nx fewer API calls"
                }
            )

        return price_data

    async def _fetch_from_provider_single(self, symbol: str, provider: MarketDataProvider) -> Optional[Dict]:
        """Fetch price data from a specific provider for a single symbol."""
        if provider.name == "yfinance":
            return await self._fetch_from_yfinance(symbol)
        elif provider.name == "alpha_vantage":
            return await self._fetch_from_alpha_vantage(symbol, provider.api_key)
        else:
            logger.warning(f"Unknown provider: {provider.name}")
            return None

    async def _fetch_from_provider(self, provider: MarketDataProvider, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Fetch price data from a specific provider with internal bulk logic."""
        if not symbols:
            return {}

        start_time = datetime.utcnow()
        results = {}

        try:
            if provider.name == "yfinance":
                # yfinance provider - handle bulk logic internally
                # yfinance has no hard limit but performance degrades with too many symbols
                YFINANCE_BULK_LIMIT = 50  # Reasonable batch size for performance

                if len(symbols) > 1:
                    # Check if we need to split into chunks due to limits
                    if len(symbols) > YFINANCE_BULK_LIMIT:
                        logger.info(f"Splitting {len(symbols)} symbols into chunks of {YFINANCE_BULK_LIMIT} for yfinance")
                        symbol_chunks = [symbols[i:i+YFINANCE_BULK_LIMIT] for i in range(0, len(symbols), YFINANCE_BULK_LIMIT)]
                        for chunk in symbol_chunks:
                            chunk_results = await self._fetch_yfinance_bulk_chunk(chunk)
                            results.update(chunk_results)
                    else:
                        # Use bulk for multiple symbols within limit
                        chunk_results = await self._fetch_yfinance_bulk_chunk(symbols)
                        results.update(chunk_results)
                else:
                    # Single symbol - use individual fetch
                    symbol = symbols[0]
                    results[symbol] = await self._fetch_from_yfinance(symbol)

            elif provider.name == "alpha_vantage":
                # Alpha Vantage provider - handle bulk logic internally
                # Alpha Vantage REALTIME_BULK_QUOTES has a 100-symbol limit
                ALPHA_VANTAGE_BULK_LIMIT = 100

                if len(symbols) > 1 and provider.api_key:
                    # Check if we're within the bulk limit
                    if len(symbols) > ALPHA_VANTAGE_BULK_LIMIT:
                        logger.warning(f"Alpha Vantage bulk fetch limited to {ALPHA_VANTAGE_BULK_LIMIT} symbols, got {len(symbols)}. Processing first {ALPHA_VANTAGE_BULK_LIMIT}.")
                        bulk_symbols = symbols[:ALPHA_VANTAGE_BULK_LIMIT]
                        remaining_symbols = symbols[ALPHA_VANTAGE_BULK_LIMIT:]

                        # Process bulk portion
                        results.update(await self._bulk_fetch_from_alpha_vantage(bulk_symbols, provider.api_key))

                        # Process remaining individually
                        for symbol in remaining_symbols:
                            try:
                                result = await self._fetch_from_alpha_vantage(symbol, provider.api_key)
                                results[symbol] = result
                                await asyncio.sleep(2)  # Rate limiting
                            except Exception as e:
                                logger.error(f"Individual fetch failed for {symbol}: {e}")
                                results[symbol] = None
                    else:
                        # Use bulk API if available and within limit
                        logger.info(f"Using Alpha Vantage bulk fetch for {len(symbols)} symbols")
                    try:
                        results = await self._bulk_fetch_from_alpha_vantage(symbols, provider.api_key)

                        # Log bulk operation
                        log_provider_activity(
                            db_session=self.db,
                            provider_id=provider.name,
                            activity_type="BULK_PRICE_UPDATE",
                            description=f"Alpha Vantage bulk fetch for {len(symbols)} symbols",
                            status="success",
                            metadata={
                                "symbols": symbols,
                                "successful_fetches": len([r for r in results.values() if r is not None]),
                                "bulk_optimization": "enabled"
                            }
                        )

                    except Exception as bulk_error:
                        logger.warning(f"Alpha Vantage bulk fetch failed: {bulk_error}, falling back to individual")
                        # Fallback to individual fetches
                        for symbol in symbols:
                            try:
                                result = await self._fetch_from_alpha_vantage(symbol, provider.api_key)
                                results[symbol] = result
                                await asyncio.sleep(2)  # Alpha Vantage rate limiting
                            except Exception as e:
                                logger.error(f"Individual fetch failed for {symbol}: {e}")
                                results[symbol] = None
                else:
                    # Single symbol or no API key - use individual fetches
                    for symbol in symbols:
                        try:
                            result = await self._fetch_from_alpha_vantage(symbol, provider.api_key)
                            results[symbol] = result
                            if len(symbols) > 1:
                                await asyncio.sleep(2)  # Rate limiting for multiple individual calls
                        except Exception as e:
                            logger.error(f"Individual fetch failed for {symbol}: {e}")
                            results[symbol] = None

            else:
                logger.warning(f"Unknown provider: {provider.name}")
                results = {symbol: None for symbol in symbols}

            return results

        except Exception as e:
            logger.error(f"Error in _fetch_from_provider for {provider.name}: {e}")
            return {symbol: None for symbol in symbols}

    async def _fetch_yfinance_bulk_chunk(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Fetch a chunk of symbols from yfinance using bulk API."""
        try:
            import yfinance as yf

            # Convert ASX symbols for yfinance
            yf_symbols = []
            for symbol in symbols:
                if not symbol.endswith('.AX') and self._is_asx_symbol(symbol):
                    yf_symbols.append(f"{symbol}.AX")
                else:
                    yf_symbols.append(symbol)

            def fetch_bulk():
                tickers = yf.Tickers(" ".join(yf_symbols))
                data = {}
                for i, original_symbol in enumerate(symbols):
                    yf_symbol = yf_symbols[i]
                    try:
                        ticker = tickers.tickers.get(yf_symbol)
                        if ticker and hasattr(ticker, 'info'):
                            info = ticker.info
                            if info and 'regularMarketPrice' in info:
                                data[original_symbol] = {
                                    "price": float(info['regularMarketPrice']),
                                    "timestamp": to_iso_string(datetime.now(timezone.utc)),
                                    "source": "yfinance_bulk"
                                }
                            else:
                                data[original_symbol] = None
                        else:
                            data[original_symbol] = None
                    except Exception as e:
                        logger.error(f"Error processing {original_symbol} in bulk chunk: {e}")
                        data[original_symbol] = None
                return data

            results = await asyncio.get_event_loop().run_in_executor(None, fetch_bulk)

            # Log bulk operation for this chunk
            log_provider_activity(
                db_session=self.db,
                provider_id="yfinance",
                activity_type="BULK_PRICE_UPDATE",
                description=f"Bulk chunk fetch completed for {len(symbols)} symbols",
                status="success",
                metadata={
                    "symbols": symbols,
                    "successful_fetches": len([r for r in results.values() if r is not None]),
                    "bulk_optimization": "enabled",
                    "chunk_size": len(symbols)
                }
            )

            return results

        except Exception as e:
            logger.error(f"Error in yfinance bulk chunk fetch: {e}")
            return {symbol: None for symbol in symbols}

    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict]:
        """Fetch price data from Yahoo Finance using yfinance library."""
        try:
            import yfinance as yf
            import asyncio

            # Run yfinance in thread pool to avoid blocking
            def fetch_data():
                # Handle ASX symbols - yfinance expects .AX suffix for ASX stocks
                yf_symbol = symbol
                if not symbol.endswith('.AX') and self._is_asx_symbol(symbol):
                    yf_symbol = f"{symbol}.AX"

                ticker = yf.Ticker(yf_symbol)

                # Get current price info
                info = ticker.info

                if not info or 'currentPrice' not in info:
                    # Fallback to history for current price
                    hist = ticker.history(period="1d")
                    if hist.empty:
                        return None

                    current_price = float(hist['Close'].iloc[-1])
                    volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                else:
                    current_price = info.get('currentPrice', 0)
                    volume = info.get('volume', 0)

                return {
                    "symbol": symbol,  # Keep original symbol format
                    "price": Decimal(str(round(current_price, 4))),
                    "volume": volume,
                    "market_cap": info.get('marketCap') if info else None,
                    "source_timestamp": utc_now(),
                    "provider": "yfinance",
                    "company_name": info.get('shortName') if info else None,
                    "currency": info.get('currency', 'AUD') if info else 'AUD'
                }

            # Run in thread pool to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, fetch_data)

            if result:
                logger.info(f"Successfully fetched {symbol} from yfinance: ${result['price']}")

            return result

        except Exception as e:
            logger.error(f"Error fetching from yfinance for {symbol}: {e}")
            return None

    def _is_asx_symbol(self, symbol: str) -> bool:
        """Check if symbol appears to be an ASX stock (basic heuristic)."""
        # ASX symbols are typically 3-4 letter codes
        # More sophisticated logic could check against known ASX symbol list
        return (len(symbol) >= 3 and len(symbol) <= 4 and
                symbol.isalpha() and symbol.isupper())

    async def _bulk_fetch_from_yfinance(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """Fetch prices for multiple symbols from yfinance in a single operation."""
        import concurrent.futures
        import asyncio

        try:
            import yfinance as yf

            def bulk_fetch():
                """Synchronous bulk fetch function to run in thread pool."""
                results = {}

                # Prepare symbol list with ASX suffixes
                yf_symbols = []
                symbol_mapping = {}

                for symbol in symbols:
                    if self._is_asx_symbol(symbol):
                        yf_symbol = f"{symbol}.AX"
                    else:
                        yf_symbol = symbol
                    yf_symbols.append(yf_symbol)
                    symbol_mapping[yf_symbol] = symbol

                try:
                    # Use yfinance bulk download - this is much more efficient!
                    tickers = yf.Tickers(' '.join(yf_symbols))

                    for yf_symbol in yf_symbols:
                        original_symbol = symbol_mapping[yf_symbol]
                        try:
                            ticker = tickers.tickers[yf_symbol]
                            info = ticker.info

                            if info and 'currentPrice' in info and info['currentPrice']:
                                price = float(info['currentPrice'])
                                results[original_symbol] = {
                                    "symbol": original_symbol,
                                    "price": price,
                                    "volume": info.get('volume', 0),
                                    "previous_close": info.get('previousClose'),
                                    "market_cap": info.get('marketCap'),
                                    "currency": info.get('currency', 'USD'),
                                    "fetched_at": datetime.utcnow(),
                                    "provider": "yfinance",
                                    "bulk_fetch": True
                                }
                            else:
                                logger.warning(f"No price data available for {original_symbol} from yfinance bulk fetch")
                                results[original_symbol] = None

                        except Exception as e:
                            logger.error(f"Error processing {original_symbol} in bulk fetch: {e}")
                            results[original_symbol] = None

                except Exception as e:
                    logger.error(f"Bulk yfinance fetch failed: {e}")
                    # Return None for all symbols on bulk failure
                    for symbol in symbols:
                        results[symbol] = None

                return results

            # Run the bulk fetch in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                results = await loop.run_in_executor(executor, bulk_fetch)

            successful_count = sum(1 for result in results.values() if result is not None)
            logger.info(f"Bulk yfinance fetch completed: {successful_count}/{len(symbols)} symbols successful")

            return results

        except ImportError:
            logger.error("yfinance not installed - cannot perform bulk fetch")
            return {symbol: None for symbol in symbols}
        except Exception as e:
            logger.error(f"Error in bulk yfinance fetch: {e}")
            return {symbol: None for symbol in symbols}

    async def _fetch_single_with_provider(self, symbol: str, provider: MarketDataProvider) -> Optional[Dict]:
        """Fetch a single symbol with a specific provider."""
        try:
            start_time = datetime.utcnow()
            price_data = await self._fetch_from_provider_single(symbol, provider)
            end_time = datetime.utcnow()

            if price_data:
                # Store in database
                await self._store_price_data(symbol, price_data, provider)

                # Log successful API usage
                self._log_api_usage(provider, symbol, 200, True)

                # Log successful activity for admin dashboard
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                log_provider_activity(
                    db_session=self.db,
                    provider_id=provider.name,
                    activity_type="API_CALL",
                    description=f"Successfully fetched {symbol} from {provider.name}: ${price_data.get('price', 'N/A')}",
                    status="success",
                    metadata={
                        "symbol": symbol,
                        "price": price_data.get('price'),
                        "provider": provider.name,
                        "response_time_ms": response_time_ms
                    }
                )

                return price_data
            else:
                # Log failed API usage
                self._log_api_usage(provider, symbol, 404, False)
                return None

        except Exception as e:
            logger.error(f"Error fetching {symbol} from {provider.name}: {e}")
            self._log_api_usage(provider, symbol, 500, False)
            return None

    async def _fetch_from_alpha_vantage(self, symbol: str, api_key: Optional[str]) -> Optional[Dict]:
        """Fetch price data from Alpha Vantage API."""
        if not api_key:
            logger.warning("Alpha Vantage API key not configured")
            return None

        try:
            session = await self.get_session()
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": api_key
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse Alpha Vantage response
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            "symbol": symbol,
                            "price": Decimal(quote.get("05. price", "0")),
                            "volume": int(quote.get("06. volume", "0")),
                            "market_cap": None,
                            "source_timestamp": utc_now(),
                            "provider": "alpha_vantage"
                        }
                    else:
                        logger.warning(f"Invalid response from Alpha Vantage for {symbol}: {data}")
                        return None
                else:
                    logger.error(f"Alpha Vantage API error {response.status} for {symbol}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage for {symbol}: {e}")
            return None

    async def _bulk_fetch_from_alpha_vantage(self, symbols: List[str], api_key: str) -> Dict[str, Optional[Dict]]:
        """Fetch prices for multiple symbols from Alpha Vantage using REALTIME_BULK_QUOTES API."""
        if not api_key:
            logger.warning("Alpha Vantage API key not configured for bulk fetch")
            return {symbol: None for symbol in symbols}

        # Alpha Vantage REALTIME_BULK_QUOTES supports up to 100 symbols
        if len(symbols) > 100:
            logger.warning(f"Alpha Vantage bulk fetch limited to 100 symbols, got {len(symbols)}. Processing first 100.")
            symbols = symbols[:100]

        try:
            session = await self.get_session()
            url = "https://www.alphavantage.co/query"

            # Join symbols with comma for bulk request
            symbols_param = ','.join(symbols)

            params = {
                "function": "REALTIME_BULK_QUOTES",
                "symbol": symbols_param,
                "apikey": api_key
            }

            logger.info(f"Making Alpha Vantage bulk request for {len(symbols)} symbols")

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = {}

                    # Parse bulk response
                    if "realtime_bulk_quotes" in data:
                        quotes = data["realtime_bulk_quotes"]

                        for symbol in symbols:
                            # Find the quote for this symbol in the response
                            symbol_data = None
                            for quote in quotes:
                                if quote.get("symbol") == symbol:
                                    symbol_data = quote
                                    break

                            if symbol_data and "price" in symbol_data:
                                try:
                                    results[symbol] = {
                                        "symbol": symbol,
                                        "price": float(symbol_data.get("price", "0")),
                                        "volume": int(symbol_data.get("volume", "0")),
                                        "change": float(symbol_data.get("change", "0")),
                                        "change_percent": symbol_data.get("change_percent", "0%"),
                                        "previous_close": float(symbol_data.get("previous_close", "0")),
                                        "market_cap": None,  # Not provided in bulk API
                                        "fetched_at": datetime.utcnow(),
                                        "provider": "alpha_vantage",
                                        "bulk_fetch": True
                                    }
                                except (ValueError, TypeError) as e:
                                    logger.error(f"Error parsing price data for {symbol}: {e}")
                                    results[symbol] = None
                            else:
                                logger.warning(f"No price data available for {symbol} in Alpha Vantage bulk response")
                                results[symbol] = None

                        successful_count = sum(1 for result in results.values() if result is not None)
                        logger.info(f"Alpha Vantage bulk fetch completed: {successful_count}/{len(symbols)} symbols successful")

                        return results

                    elif "Error Message" in data:
                        logger.error(f"Alpha Vantage bulk API error: {data['Error Message']}")
                        return {symbol: None for symbol in symbols}
                    elif "Note" in data:
                        logger.warning(f"Alpha Vantage bulk API rate limit: {data['Note']}")
                        return {symbol: None for symbol in symbols}
                    else:
                        logger.error(f"Unexpected Alpha Vantage bulk response format: {data}")
                        return {symbol: None for symbol in symbols}

                else:
                    logger.error(f"Alpha Vantage bulk API HTTP error {response.status}")
                    return {symbol: None for symbol in symbols}

        except Exception as e:
            logger.error(f"Error in Alpha Vantage bulk fetch: {e}")
            return {symbol: None for symbol in symbols}

    async def _store_price_data(self, symbol: str, price_data: Dict, provider: MarketDataProvider):
        """Store price data in the database."""
        try:
            price_record = RealtimePriceHistory(
                symbol=symbol,
                price=price_data["price"],
                volume=price_data.get("volume"),
                market_cap=price_data.get("market_cap"),
                provider_id=provider.id,
                source_timestamp=price_data["source_timestamp"],
                fetched_at=datetime.utcnow()
            )

            self.db.add(price_record)
            self.db.commit()

            logger.info(f"Stored price data for {symbol}: ${price_data['price']}")

        except Exception as e:
            logger.error(f"Error storing price data for {symbol}: {e}")
            self.db.rollback()

    def _log_api_usage(self, provider: MarketDataProvider, symbol: str, status_code: int,
                      success: bool, error_message: Optional[str] = None):
        """Log API usage for monitoring and rate limiting."""
        try:
            # Use local time for consistency with recorded_at field
            now_local = utc_now()

            # Create the usage record with explicit recorded_at to ensure consistency
            # Both recorded_at and time_bucket must be in same timezone format
            usage_record = ApiUsageMetrics(
                metric_id=f"{provider.name}_{symbol}_{now_local.strftime('%Y%m%d_%H%M%S_%f')[:23]}",  # Include microseconds for uniqueness
                provider_id=provider.name,
                request_type="price_fetch",
                requests_count=1,
                data_points_fetched=1 if success else 0,
                recorded_at=now_local,
                time_bucket="hourly",  # Use string value as required by database constraint
                rate_limit_hit=False,
                error_count=1 if not success else 0,
                avg_response_time_ms=None  # Would be calculated in real implementation
            )

            self.db.add(usage_record)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            self.db.rollback()

    def get_latest_price(self, symbol: str, max_age_minutes: int = 30) -> Optional[RealtimePriceHistory]:
        """Get the latest cached price for a symbol."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

        return self.db.query(RealtimePriceHistory).filter(
            and_(
                RealtimePriceHistory.symbol == symbol,
                RealtimePriceHistory.fetched_at >= cutoff_time
            )
        ).order_by(desc(RealtimePriceHistory.fetched_at)).first()

    def get_price_history(self, symbol: str, days: int = 7) -> List[RealtimePriceHistory]:
        """Get price history for a symbol over the specified number of days."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        return self.db.query(RealtimePriceHistory).filter(
            and_(
                RealtimePriceHistory.symbol == symbol,
                RealtimePriceHistory.fetched_at >= cutoff_time
            )
        ).order_by(desc(RealtimePriceHistory.fetched_at)).all()

    async def refresh_portfolio_symbols(self, symbols: List[str]) -> Dict[str, Dict]:
        """Refresh prices for all symbols in user portfolios."""
        logger.info(f"Refreshing prices for {len(symbols)} symbols")

        # Filter out symbols that have fresh data (less than 15 minutes old)
        symbols_to_fetch = []
        fresh_prices = {}

        for symbol in symbols:
            latest = self.get_latest_price(symbol, max_age_minutes=15)
            if latest:
                fresh_prices[symbol] = {
                    "symbol": symbol,
                    "price": latest.price,
                    "volume": latest.volume,
                    "fetched_at": latest.fetched_at,
                    "cached": True
                }
            else:
                symbols_to_fetch.append(symbol)

        # Fetch new data for stale symbols
        if symbols_to_fetch:
            new_prices = await self.fetch_multiple_prices(symbols_to_fetch)
            fresh_prices.update(new_prices)

        return fresh_prices


# Helper functions for activity logging (used by tests)
def make_api_call(provider_config: dict, symbol: str) -> dict:
    """
    Make an actual API call to the market data provider.

    This is a mock function for testing. In production, this would contain
    the actual implementation for each provider (Alpha Vantage, yfinance, etc.)
    """
    # Mock implementation - in reality this would make HTTP requests
    if provider_config.get('simulate_error'):
        raise Exception("API rate limit exceeded")

    return {
        "price": 150.25,
        "timestamp": to_iso_string(datetime.now(timezone.utc))
    }


def fetch_price_with_logging(
    db_session: Session,
    provider_id: str,
    symbol: str
) -> Optional[Dict]:
    """
    Fetch price data from a market data provider with activity logging.

    Args:
        db_session: Database session
        provider_id: ID of the market data provider
        symbol: Stock symbol to fetch

    Returns:
        Price data dictionary or None if failed
    """
    try:
        # In a real implementation, we'd get provider config from the database
        provider_config = {"endpoint": "https://api.example.com"}

        # Make the API call
        start_time = datetime.utcnow()
        result = make_api_call(provider_config, symbol)
        end_time = datetime.utcnow()

        # Calculate response time
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Log successful activity
        log_provider_activity(
            db_session=db_session,
            provider_id=provider_id,
            activity_type="API_CALL",
            description=f"Successfully fetched price for {symbol}",
            status="success",
            metadata={
                "symbol": symbol,
                "price": str(result.get("price", 0)),
                "response_time_ms": response_time_ms
            }
        )

        return result

    except Exception as e:
        # Log error activity
        log_provider_activity(
            db_session=db_session,
            provider_id=provider_id,
            activity_type="API_ERROR",
            description=f"Failed to fetch {symbol} price: {str(e)}",
            status="error",
            metadata={
                "symbol": symbol,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

        # Re-raise the exception for the caller to handle
        raise


def log_rate_limit_hit(db_session: Session, provider_id: str, wait_time: int):
    """
    Log when a provider hits its rate limit.

    Args:
        db_session: Database session
        provider_id: ID of the market data provider
        wait_time: Time to wait before next request (seconds)
    """
    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="RATE_LIMIT",
        description=f"Rate limit reached, waiting {wait_time} seconds",
        status="warning",
        metadata={
            "wait_time": wait_time,
            "throttled": True
        }
    )
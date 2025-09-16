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
from src.models.realtime_symbol import RealtimeSymbol
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.utils.datetime_utils import to_iso_string
from src.models.holding import Holding
from src.models.stock import Stock
from src.models.portfolio import Portfolio
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

                    # Store in database using new single master table approach
                    self.store_price_to_master(symbol, price_data, provider)

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

    def get_actively_monitored_symbols(self, provider_bulk_limit: int = 10, minutes_lookback: int = 60) -> List[str]:
        """
        Get list of symbols that should be actively monitored based on:
        1. Current portfolio holdings
        2. Recent price requests

        Args:
            provider_bulk_limit: Maximum symbols per batch (provider-specific)
            minutes_lookback: How far back to look for recent price requests

        Returns:
            List of symbol strings to monitor, limited by provider_bulk_limit
        """
        monitored_symbols = set()

        # 1. Get symbols from active portfolio holdings
        portfolio_symbols = (
            self.db.query(Stock.symbol)
            .join(Holding, Holding.stock_id == Stock.id)
            .join(Portfolio, Portfolio.id == Holding.portfolio_id)
            .filter(Holding.quantity > 0)  # Only active holdings
            .distinct()
            .all()
        )

        for symbol_tuple in portfolio_symbols:
            monitored_symbols.add(symbol_tuple[0])

        # 2. Get symbols from recent price requests (last X minutes)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_lookback)
        recent_symbols = (
            self.db.query(RealtimePriceHistory.symbol)
            .filter(RealtimePriceHistory.fetched_at >= cutoff_time)
            .distinct()
            .all()
        )

        for symbol_tuple in recent_symbols:
            monitored_symbols.add(symbol_tuple[0])

        # Convert to sorted list for consistent ordering
        symbol_list = sorted(list(monitored_symbols))

        # Limit to provider bulk limit
        return symbol_list[:provider_bulk_limit]

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
                            # Store in database using new single master table approach
                            self.store_price_to_master(symbol, result, provider)
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

            # Trigger bulk portfolio updates for all successfully fetched symbols
            successful_symbols = list(price_data.keys())
            if successful_symbols:
                self._trigger_bulk_portfolio_updates(successful_symbols)

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
                hist = None

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

                # Get opening price with fallback strategy
                opening_price = None
                if info and info.get('open'):
                    opening_price = info.get('open')
                elif info and info.get('regularMarketOpen'):
                    opening_price = info.get('regularMarketOpen')
                elif hist is not None and not hist.empty and 'Open' in hist.columns:
                    opening_price = float(hist['Open'].iloc[-1])
                elif hist is None:  # Need to fetch history if not already done
                    hist = ticker.history(period="1d")
                    if not hist.empty and 'Open' in hist.columns:
                        opening_price = float(hist['Open'].iloc[-1])

                # Get other price fields with similar fallback strategy
                high_price = None
                if info and info.get('dayHigh'):
                    high_price = info.get('dayHigh')
                elif hist is not None and not hist.empty and 'High' in hist.columns:
                    high_price = float(hist['High'].iloc[-1])

                low_price = None
                if info and info.get('dayLow'):
                    low_price = info.get('dayLow')
                elif hist is not None and not hist.empty and 'Low' in hist.columns:
                    low_price = float(hist['Low'].iloc[-1])

                previous_close = None
                if info and info.get('previousClose'):
                    previous_close = info.get('previousClose')

                return {
                    "symbol": symbol,  # Keep original symbol format
                    "price": Decimal(str(round(current_price, 4))),

                    # Extended price information for trend calculations
                    "open_price": Decimal(str(round(opening_price, 4))) if opening_price is not None else None,
                    "high_price": Decimal(str(round(high_price, 4))) if high_price is not None else None,
                    "low_price": Decimal(str(round(low_price, 4))) if low_price is not None else None,
                    "previous_close": Decimal(str(round(previous_close, 4))) if previous_close is not None else None,

                    # Volume and market data
                    "volume": volume,
                    "market_cap": info.get('marketCap') if info else None,

                    # Extended market information
                    "fifty_two_week_high": Decimal(str(round(info.get('fiftyTwoWeekHigh', current_price), 4))) if info and info.get('fiftyTwoWeekHigh') else None,
                    "fifty_two_week_low": Decimal(str(round(info.get('fiftyTwoWeekLow', current_price), 4))) if info and info.get('fiftyTwoWeekLow') else None,
                    "dividend_yield": Decimal(str(round(info.get('dividendYield', 0) * 100, 2))) if info and info.get('dividendYield') else None,
                    "pe_ratio": Decimal(str(round(info.get('trailingPE', 0), 2))) if info and info.get('trailingPE') else None,
                    "beta": Decimal(str(round(info.get('beta', 1.0), 2))) if info and info.get('beta') else None,

                    # Metadata
                    "currency": info.get('currency', 'AUD') if info else 'AUD',
                    "company_name": info.get('shortName') if info else None,

                    # System fields
                    "source_timestamp": utc_now(),
                    "provider": "yfinance"
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
        # Common ASX symbols that we know about
        known_asx_symbols = {
            'CBA', 'ANZ', 'WBC', 'NAB',  # Big 4 banks
            'BHP', 'RIO', 'FMG',         # Mining
            'CSL', 'COH', 'PME',         # Healthcare
            'WOW', 'COL', 'JBH',         # Retail
            'TCL', 'TLS', 'SGP',         # Telco/Property
            'MQG', 'SUN', 'QBE',         # Finance/Insurance
            'REA', 'CAR', 'SEK',         # Tech/Services
            'GMG', 'WES', 'ALL',         # Industrials
            'APT', 'XRO', 'WTC',         # Fintech
            'A2M', 'BAP', 'IFL'          # Other
        }

        # Check if it's a known ASX symbol
        if symbol in known_asx_symbols:
            return True

        # Fallback heuristic: 3-4 letter codes, but exclude common US patterns
        us_patterns = {'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC'}
        if symbol in us_patterns:
            return False

        # For unknown symbols, use basic heuristic but be more conservative
        # ASX symbols are typically 3-4 letters, but so are many US symbols
        # This is a fallback that may need refinement
        return (len(symbol) == 3 and symbol.isalpha() and symbol.isupper())

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

                            price = None
                            if info and 'regularMarketPrice' in info and info['regularMarketPrice']:
                                price = float(info['regularMarketPrice'])
                            elif info and 'currentPrice' in info and info['currentPrice']:
                                price = float(info['currentPrice'])

                            if price:
                                results[original_symbol] = {
                                    "symbol": original_symbol,
                                    "price": price,
                                    "volume": info.get('volume', 0),
                                    "previous_close": info.get('previousClose'),
                                    "market_cap": info.get('marketCap'),
                                    "currency": info.get('currency', 'USD'),
                                    "fetched_at": to_iso_string(datetime.utcnow()),
                                    "source_timestamp": utc_now(),
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
                # Store in database using new single master table approach
                self.store_price_to_master(symbol, price_data, provider)

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
                        "price": str(price_data.get('price')) if price_data.get('price') is not None else None,
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
                                        "fetched_at": to_iso_string(datetime.utcnow()),
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


    def store_price_to_master(self, symbol: str, price_data: Dict, provider: MarketDataProvider) -> RealtimeSymbol:
        """
        Store price data using single master table approach (Option C).

        This method implements the new single-write pattern that eliminates
        dual-table synchronization complexity. It writes to realtime_symbols
        as the single source of truth and maintains a reference to history.
        """
        try:
            # First, create history record to maintain time-series data
            history_record = RealtimePriceHistory(
                symbol=symbol,
                price=price_data["price"],
                opening_price=price_data.get("open_price"),
                high_price=price_data.get("high_price"),
                low_price=price_data.get("low_price"),
                previous_close=price_data.get("previous_close"),
                volume=price_data.get("volume"),
                market_cap=price_data.get("market_cap"),
                fifty_two_week_high=price_data.get("fifty_two_week_high"),
                fifty_two_week_low=price_data.get("fifty_two_week_low"),
                dividend_yield=price_data.get("dividend_yield"),
                pe_ratio=price_data.get("pe_ratio"),
                beta=price_data.get("beta"),
                currency=price_data.get("currency", "USD"),
                company_name=price_data.get("company_name"),
                provider_id=provider.id,
                source_timestamp=price_data["source_timestamp"],
                fetched_at=utc_now()
            )
            self.db.add(history_record)
            self.db.flush()  # Get the history record ID

            # Now update or create master table record (single source of truth)
            master_record = self.db.query(RealtimeSymbol).filter_by(symbol=symbol).first()

            if master_record:
                # Update existing master record
                master_record.current_price = price_data["price"]
                master_record.company_name = price_data.get("company_name") or master_record.company_name
                master_record.last_updated = price_data["source_timestamp"]
                master_record.provider_id = provider.id
                master_record.volume = price_data.get("volume")
                master_record.market_cap = price_data.get("market_cap")
                master_record.latest_history_id = history_record.id
                master_record.update_timestamp()  # Update the updated_at field

                logger.info(f"Updated master symbol record for {symbol}: ${price_data['price']}")
            else:
                # Create new master record
                master_record = RealtimeSymbol(
                    symbol=symbol,
                    current_price=price_data["price"],
                    company_name=price_data.get("company_name", f"{symbol} Company"),
                    last_updated=price_data["source_timestamp"],
                    provider_id=provider.id,
                    volume=price_data.get("volume"),
                    market_cap=price_data.get("market_cap"),
                    latest_history_id=history_record.id
                )
                self.db.add(master_record)

                logger.info(f"Created new master symbol record for {symbol}: ${price_data['price']}")

            self.db.commit()

            logger.info(f"Stored price data to master table for {symbol}: ${price_data['price']}")

            # Trigger portfolio updates for this symbol
            self._trigger_portfolio_updates(symbol)

            return master_record

        except Exception as e:
            logger.error(f"Error storing price data to master table for {symbol}: {e}")
            self.db.rollback()
            raise

    def get_current_price_from_master(self, symbol: str) -> Optional[Dict]:
        """
        Get current price data from master table (single source of truth).

        Returns price data from realtime_symbols table, ensuring consistent
        pricing across all APIs and portfolio calculations.
        """
        try:
            master_record = self.db.query(RealtimeSymbol).filter_by(symbol=symbol).first()

            if not master_record:
                return None

            return {
                "symbol": master_record.symbol,
                "price": master_record.current_price,
                "company_name": master_record.company_name,
                "fetched_at": master_record.last_updated,
                "volume": master_record.volume,
                "market_cap": master_record.market_cap,
                "provider": master_record.provider.display_name if master_record.provider else None
            }

        except Exception as e:
            logger.error(f"Error getting current price from master table for {symbol}: {e}")
            return None

    def _store_comprehensive_price_data(self, symbol: str, price_data: Dict, provider: MarketDataProvider, db_session: Session) -> RealtimePriceHistory:
        """Store comprehensive price data with custom session (for testing)."""
        try:
            # Create price history record
            price_record = RealtimePriceHistory(
                symbol=symbol,
                price=price_data["price"],

                # Extended price information for trend calculations
                opening_price=price_data.get("open_price"),
                high_price=price_data.get("high_price"),
                low_price=price_data.get("low_price"),
                previous_close=price_data.get("previous_close"),

                # Volume and market data
                volume=price_data.get("volume"),
                market_cap=price_data.get("market_cap"),

                # Extended market information
                fifty_two_week_high=price_data.get("fifty_two_week_high"),
                fifty_two_week_low=price_data.get("fifty_two_week_low"),
                dividend_yield=price_data.get("dividend_yield"),
                pe_ratio=price_data.get("pe_ratio"),
                beta=price_data.get("beta"),

                # Metadata
                currency=price_data.get("currency", "USD"),
                company_name=price_data.get("company_name"),

                # System fields
                provider_id=provider.id,
                source_timestamp=price_data["source_timestamp"],
                fetched_at=utc_now()
            )

            db_session.add(price_record)

            # CRITICAL FIX: Also update stocks table so holdings show fresh timestamps
            # Find existing stock record or create new one
            stock = db_session.query(Stock).filter_by(symbol=symbol).first()

            if stock:
                # Update existing stock with fresh price and timestamp
                stock.current_price = price_data["price"]
                stock.last_price_update = price_data["source_timestamp"]
                logger.info(f"Updated stock table for {symbol}: ${price_data['price']}")
            else:
                # Create new stock record for new symbols
                stock = Stock(
                    symbol=symbol,
                    company_name=price_data.get("company_name", f"{symbol} Company"),
                    exchange="ASX" if symbol.endswith(".AX") else "NASDAQ",  # Simple heuristic
                    current_price=price_data["price"],
                    last_price_update=price_data["source_timestamp"]
                )
                db_session.add(stock)
                logger.info(f"Created new stock record for {symbol}: ${price_data['price']}")

            db_session.commit()
            logger.info(f"Stored comprehensive price data for {symbol}: ${price_data['price']}")
            return price_record

        except Exception as e:
            logger.error(f"Error storing comprehensive price data for {symbol}: {e}")
            db_session.rollback()
            raise

    def get_latest_opening_price(self, symbol: str) -> Optional[Decimal]:
        """Get the latest opening price for a symbol."""
        record = self.db.query(RealtimePriceHistory)\
            .filter(RealtimePriceHistory.symbol == symbol)\
            .order_by(desc(RealtimePriceHistory.fetched_at))\
            .first()
        return record.opening_price if record else None

    def get_latest_price_value(self, symbol: str) -> Optional[Decimal]:
        """Get the latest current price value for a symbol."""
        record = self.db.query(RealtimePriceHistory)\
            .filter(RealtimePriceHistory.symbol == symbol)\
            .order_by(desc(RealtimePriceHistory.fetched_at))\
            .first()
        return record.price if record else None

    def _log_api_usage(self, provider: MarketDataProvider, symbol: str, status_code: int,
                      success: bool, error_message: Optional[str] = None):
        """Log API usage for monitoring and rate limiting."""
        try:
            # Use local time for consistency with recorded_at field
            now_local = utc_now()

            # Create the usage record with explicit recorded_at to ensure consistency
            # Both recorded_at and time_bucket must be in same timezone format
            usage_record = MarketDataUsageMetrics(
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
                    "fetched_at": to_iso_string(latest.fetched_at),
                    "cached": True
                }
            else:
                symbols_to_fetch.append(symbol)

        # Fetch new data for stale symbols
        if symbols_to_fetch:
            new_prices = await self.fetch_multiple_prices(symbols_to_fetch)
            fresh_prices.update(new_prices)

        return fresh_prices

    def _trigger_portfolio_updates(self, symbol: str):
        """
        Trigger real-time portfolio updates for a symbol using the update queue.
        This method is called after price data is stored to update affected portfolios.
        """
        try:
            from src.services.portfolio_update_queue import get_portfolio_update_queue
            from src.services.real_time_portfolio_service import RealTimePortfolioService

            # Find portfolios that contain this symbol
            portfolio_service = RealTimePortfolioService(self.db)
            affected_portfolios = portfolio_service._find_portfolios_with_symbol(symbol)

            if affected_portfolios:
                # Queue updates for each affected portfolio instead of executing immediately
                queue = get_portfolio_update_queue()

                for portfolio in affected_portfolios:
                    queued = queue.queue_portfolio_update(
                        portfolio_id=str(portfolio.id),
                        symbols=[symbol],
                        priority=1  # Normal priority for price updates
                    )

                    if queued:
                        logger.debug(f"Queued portfolio update for {portfolio.id} after {symbol} price change")
                    else:
                        logger.warning(f"Rate limited portfolio update for {portfolio.id} after {symbol} price change")

                logger.info(f"Queued portfolio updates for {len(affected_portfolios)} portfolios after {symbol} price change")

        except Exception as e:
            logger.error(f"Error queuing portfolio updates for symbol {symbol}: {e}")
            # Don't re-raise - this should not fail the price storage operation

    def _trigger_bulk_portfolio_updates(self, symbols: List[str]):
        """
        Trigger bulk real-time portfolio updates for multiple symbols using the queue.
        More efficient than individual updates when multiple prices change.
        """
        try:
            from src.services.portfolio_update_queue import get_portfolio_update_queue
            from src.services.real_time_portfolio_service import RealTimePortfolioService

            # Find all unique portfolios affected by these symbols
            portfolio_service = RealTimePortfolioService(self.db)
            all_affected_portfolios = set()

            for symbol in symbols:
                portfolios = portfolio_service._find_portfolios_with_symbol(symbol)
                all_affected_portfolios.update(portfolios)

            if all_affected_portfolios:
                # Queue bulk updates for each affected portfolio
                queue = get_portfolio_update_queue()
                queued_count = 0

                for portfolio in all_affected_portfolios:
                    # Find which symbols from the bulk update affect this portfolio
                    portfolio_symbols = []
                    for symbol in symbols:
                        symbol_portfolios = portfolio_service._find_portfolios_with_symbol(symbol)
                        if portfolio in symbol_portfolios:
                            portfolio_symbols.append(symbol)

                    if portfolio_symbols:
                        queued = queue.queue_portfolio_update(
                            portfolio_id=str(portfolio.id),
                            symbols=portfolio_symbols,
                            priority=2  # Higher priority for bulk operations
                        )

                        if queued:
                            queued_count += 1

                logger.info(f"Queued bulk portfolio updates for {queued_count}/{len(all_affected_portfolios)} unique portfolios after {len(symbols)} price changes")

        except Exception as e:
            logger.error(f"Error queuing bulk portfolio updates for symbols {symbols}: {e}")
            # Don't re-raise - this should not fail the price storage operation


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
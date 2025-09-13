"""
Market data service for fetching and managing stock price data.

Provides abstraction layer for different market data providers
with fallback support and caching.
"""

from datetime import datetime, timedelta
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
from src.core.logging import get_logger

logger = get_logger(__name__)


class MarketDataService:
    """Service for fetching and managing market data."""

    def __init__(self, db: Session):
        self.db = db
        self._session: Optional[aiohttp.ClientSession] = None

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

    async def fetch_price(self, symbol: str) -> Optional[Dict]:
        """Fetch current price for a symbol using available providers."""
        providers = self.get_enabled_providers()

        for provider in providers:
            try:
                price_data = await self._fetch_from_provider(symbol, provider)
                if price_data:
                    # Store in database
                    await self._store_price_data(symbol, price_data, provider)

                    # Log successful API usage
                    self._log_api_usage(provider, symbol, 200, True)

                    return price_data

            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} from {provider.name}: {e}")
                # Log failed API usage
                self._log_api_usage(provider, symbol, 500, False, str(e))
                continue

        logger.error(f"Failed to fetch price for {symbol} from all providers")
        return None

    async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch prices for multiple symbols concurrently."""
        tasks = [self.fetch_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        price_data = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                price_data[symbol] = result
            elif isinstance(result, Exception):
                logger.error(f"Error fetching {symbol}: {result}")

        return price_data

    async def _fetch_from_provider(self, symbol: str, provider: MarketDataProvider) -> Optional[Dict]:
        """Fetch price data from a specific provider."""
        if provider.name == "yfinance":
            return await self._fetch_from_yfinance(symbol)
        elif provider.name == "alpha_vantage":
            return await self._fetch_from_alpha_vantage(symbol, provider.api_key)
        else:
            logger.warning(f"Unknown provider: {provider.name}")
            return None

    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict]:
        """Fetch price data from Yahoo Finance (via yfinance-like API)."""
        try:
            session = await self.get_session()

            # Mock implementation - in real implementation would use yfinance
            # For development, return mock data
            import random
            base_price = 100 + hash(symbol) % 900  # Deterministic base price
            price_variation = random.uniform(-5, 5)
            current_price = base_price + price_variation

            return {
                "symbol": symbol,
                "price": Decimal(str(round(current_price, 2))),
                "volume": random.randint(1000000, 10000000),
                "market_cap": None,
                "source_timestamp": datetime.now(),
                "provider": "yfinance"
            }

        except Exception as e:
            logger.error(f"Error fetching from yfinance for {symbol}: {e}")
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
                            "source_timestamp": datetime.now(),
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
            usage_record = ApiUsageMetrics(
                provider_name=provider.name,
                symbol=symbol,
                endpoint="price_fetch",
                request_timestamp=datetime.utcnow(),
                response_status=status_code,
                success=success,
                error_message=error_message,
                response_time_ms=None,  # Would be calculated in real implementation
                rate_limit_remaining=None,  # Would be extracted from response headers
                rate_limit_total=provider.rate_limit_per_day
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
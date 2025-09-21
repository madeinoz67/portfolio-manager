"""
Adapter-based market data service for fetching and managing stock price data.

This service uses the new adapter architecture to provide a drop-in replacement
for the legacy MarketDataService, integrating with the provider registry and
configuration system for modern market data operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import asyncio
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from src.models.realtime_price_history import RealtimePriceHistory
from src.models.realtime_symbol import RealtimeSymbol
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.utils.datetime_utils import to_iso_string, utc_now
from src.models.holding import Holding
from src.models.stock import Stock
from src.models.portfolio import Portfolio
from src.services.activity_service import log_provider_activity
from src.core.logging import get_logger

# New adapter imports
from src.services.adapters.registry import get_provider_registry
from src.services.adapters.base_adapter import AdapterResponse
from src.models.provider_configuration import ProviderConfiguration

logger = get_logger(__name__)


class AdapterMarketDataService:
    """
    New adapter-based market data service.

    Drop-in replacement for legacy MarketDataService that uses the new
    adapter architecture for provider management and price fetching.
    """

    def __init__(self, db: Session):
        self.db = db
        self.registry = get_provider_registry()
        self._recent_fetches = {}  # Track recent fetches to avoid duplicates

    async def close_session(self):
        """Close any open sessions (compatibility method)."""
        # Adapter system manages its own sessions
        pass

    def get_actively_monitored_symbols(
        self,
        provider_bulk_limit: int = 50,
        minutes_lookback: int = 60
    ) -> List[str]:
        """
        Get symbols that should be actively monitored for price updates.

        This includes portfolio holdings and recently requested symbols.
        Compatible interface with legacy MarketDataService.
        """
        symbols = set()

        # Get all symbols from portfolio holdings
        try:
            portfolio_holdings = (
                self.db.query(Stock.symbol)
                .join(Holding, Stock.id == Holding.stock_id)
                .join(Portfolio, Holding.portfolio_id == Portfolio.id)
                .distinct()
                .all()
            )

            for holding in portfolio_holdings:
                symbols.add(holding.symbol)

        except Exception as e:
            logger.error(f"Failed to get portfolio holdings: {e}")

        # Get recently requested symbols (within lookback period)
        try:
            lookback_time = utc_now() - timedelta(minutes=minutes_lookback)
            recent_symbols = (
                self.db.query(RealtimeSymbol.symbol)
                .filter(RealtimeSymbol.last_updated >= lookback_time.replace(tzinfo=None))
                .distinct()
                .all()
            )

            for symbol_record in recent_symbols:
                symbols.add(symbol_record.symbol)

        except Exception as e:
            logger.error(f"Failed to get recent symbols: {e}")

        result = list(symbols)[:provider_bulk_limit]
        logger.info(f"Found {len(result)} actively monitored symbols: {result}")
        return result

    async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Fetch prices for multiple symbols using adapter system.

        Args:
            symbols: List of stock symbols to fetch

        Returns:
            Dictionary mapping symbols to price data
        """
        if not symbols:
            return {}

        results = {}

        # Get active provider configurations
        active_configs = (
            self.db.query(ProviderConfiguration)
            .filter(ProviderConfiguration.is_active == True)
            .all()
        )

        if not active_configs:
            logger.warning("No active provider configurations found")
            return {}

        # Try each provider until we get results
        for config in active_configs:
            try:
                provider_name = config.provider_name
                logger.info(f"Fetching {len(symbols)} symbols using adapter: {provider_name}")

                # Get adapter instance from registry
                adapter = await self.registry.get_provider_instance(provider_name)
                if not adapter:
                    logger.warning(f"No adapter instance available for {provider_name}")
                    continue

                # Use bulk fetch if supported
                if adapter.capabilities.supports_bulk_quotes and len(symbols) > 1:
                    response = await adapter.fetch_bulk_quotes(symbols)
                    if response.success and response.data:
                        bulk_results = response.data.get('quotes', {})

                        # Process bulk results
                        for symbol in symbols:
                            if symbol in bulk_results:
                                quote_data = bulk_results[symbol]

                                # Convert adapter response to legacy format
                                price_data = self._convert_adapter_response(quote_data, symbol, provider_name)
                                if price_data:
                                    results[symbol] = price_data
                                    # Store to database
                                    self._store_price_to_master(symbol, price_data, provider_name)

                        logger.info(f"Bulk fetch successful: {len(results)}/{len(symbols)} symbols")
                        break  # Success, don't try other providers

                else:
                    # Fall back to individual fetches
                    for symbol in symbols:
                        try:
                            response = await adapter.fetch_quote(symbol)
                            if response.success and response.data:
                                # Convert adapter response to legacy format
                                price_data = self._convert_adapter_response(
                                    response.data, symbol, provider_name
                                )
                                if price_data:
                                    results[symbol] = price_data
                                    # Store to database
                                    self._store_price_to_master(symbol, price_data, provider_name)

                        except Exception as e:
                            logger.error(f"Failed to fetch {symbol} from {provider_name}: {e}")

                    if results:
                        logger.info(f"Individual fetches successful: {len(results)}/{len(symbols)} symbols")
                        break  # Success, don't try other providers

            except Exception as e:
                logger.error(f"Provider {config.provider_name} failed: {e}")
                continue

        # Log usage metrics for successful fetches
        if results:
            self._log_usage_metrics(results, active_configs[0].provider_name)

        return results

    def _convert_adapter_response(
        self,
        adapter_data: Dict,
        symbol: str,
        provider_name: str
    ) -> Optional[Dict]:
        """
        Convert new adapter response format to legacy price data format.

        Args:
            adapter_data: Data from adapter response
            symbol: Stock symbol
            provider_name: Name of provider

        Returns:
            Price data in legacy format
        """
        try:
            # Handle different adapter response formats
            if 'price' in adapter_data:
                price = adapter_data['price']
            elif 'regularMarketPrice' in adapter_data:
                price = adapter_data['regularMarketPrice']
            elif 'last' in adapter_data:
                price = adapter_data['last']
            else:
                logger.warning(f"No price field found in adapter data for {symbol}")
                return None

            # Build legacy format response
            return {
                'symbol': symbol,
                'price': float(price),
                'open': adapter_data.get('open', adapter_data.get('regularMarketOpen')),
                'high': adapter_data.get('high', adapter_data.get('regularMarketDayHigh')),
                'low': adapter_data.get('low', adapter_data.get('regularMarketDayLow')),
                'volume': adapter_data.get('volume', adapter_data.get('regularMarketVolume')),
                'market_cap': adapter_data.get('marketCap'),
                'company_name': adapter_data.get('longName', adapter_data.get('shortName')),
                'currency': adapter_data.get('currency', 'USD'),
                'source_timestamp': utc_now().replace(tzinfo=None),
                'provider': provider_name
            }

        except Exception as e:
            logger.error(f"Failed to convert adapter response for {symbol}: {e}")
            return None

    def _store_price_to_master(self, symbol: str, price_data: Dict, provider_name: str):
        """
        Store price data to master realtime_symbols table.

        Args:
            symbol: Stock symbol
            price_data: Price data dictionary
            provider_name: Name of data provider
        """
        try:
            now = utc_now().replace(tzinfo=None)

            # Update or create master record
            master_record = self.db.query(RealtimeSymbol).filter(
                RealtimeSymbol.symbol == symbol
            ).first()

            if master_record:
                # Update existing record
                master_record.current_price = Decimal(str(price_data['price']))
                master_record.last_updated = now
                master_record.volume = price_data.get('volume')
                master_record.market_cap = price_data.get('market_cap')
                master_record.company_name = price_data.get('company_name')
                master_record.currency = price_data.get('currency', 'USD')
                master_record.provider = provider_name
            else:
                # Create new record
                master_record = RealtimeSymbol(
                    symbol=symbol,
                    current_price=Decimal(str(price_data['price'])),
                    last_updated=now,
                    volume=price_data.get('volume'),
                    market_cap=price_data.get('market_cap'),
                    company_name=price_data.get('company_name'),
                    currency=price_data.get('currency', 'USD'),
                    provider=provider_name
                )
                self.db.add(master_record)

            # Store historical record
            history_record = RealtimePriceHistory(
                symbol=symbol,
                price=Decimal(str(price_data['price'])),
                fetched_at=now,
                open_price=Decimal(str(price_data['open'])) if price_data.get('open') else None,
                high_price=Decimal(str(price_data['high'])) if price_data.get('high') else None,
                low_price=Decimal(str(price_data['low'])) if price_data.get('low') else None,
                volume=price_data.get('volume'),
                provider=provider_name
            )
            self.db.add(history_record)

            self.db.commit()
            logger.debug(f"Stored price data for {symbol}: ${price_data['price']}")

        except Exception as e:
            logger.error(f"Failed to store price data for {symbol}: {e}")
            self.db.rollback()

    def _log_usage_metrics(self, results: Dict[str, Dict], provider_name: str):
        """
        Log usage metrics for adapter operations.

        Args:
            results: Dictionary of successful price fetches
            provider_name: Name of provider used
        """
        try:
            now = utc_now().replace(tzinfo=None)

            # Create usage metrics record
            metrics = MarketDataUsageMetrics(
                provider_name=provider_name,
                requests_count=len(results),
                successful_requests=len(results),
                error_count=0,
                avg_response_time_ms=100.0,  # Default reasonable value
                cost_estimate=Decimal('0.00'),  # Free for most providers
                recorded_at=now
            )

            self.db.add(metrics)
            self.db.commit()

            # Log activity for admin dashboard
            log_provider_activity(
                db_session=self.db,
                provider_id=provider_name,
                activity_type="BULK_PRICE_UPDATE",
                description=f"Successfully fetched {len(results)} symbols via adapter system",
                status="success",
                metadata={
                    "symbols_count": len(results),
                    "symbols": list(results.keys()),
                    "adapter_system": True
                }
            )

        except Exception as e:
            logger.error(f"Failed to log usage metrics: {e}")
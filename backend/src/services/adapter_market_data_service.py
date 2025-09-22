"""
Adapter-based market data service for fetching and managing stock price data.

This service uses the new adapter architecture to provide a drop-in replacement
for the legacy MarketDataService, integrating with the provider registry and
configuration system for modern market data operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import decimal
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

        This includes all existing symbols in realtime_symbols table, portfolio holdings,
        and recently requested symbols. No fallback logic - processes all existing market data.
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

        # ALWAYS include all existing symbols from realtime_symbols table (no fallback logic)
        try:
            all_existing_symbols = (
                self.db.query(RealtimeSymbol.symbol)
                .distinct()
                .all()
            )

            for symbol_record in all_existing_symbols:
                symbols.add(symbol_record.symbol)

            logger.debug(f"Added {len(all_existing_symbols)} existing symbols from realtime_symbols table")

        except Exception as e:
            logger.error(f"Failed to get all existing symbols: {e}")

        result = list(symbols)[:provider_bulk_limit]
        logger.info(f"Found {len(result)} actively monitored symbols (portfolios + recent + all existing): {result}")
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
        # Try a more direct query approach that works with SQLite boolean values
        try:
            # Use raw SQL to bypass any SQLAlchemy boolean conversion issues
            active_configs = (
                self.db.query(ProviderConfiguration)
                .filter(ProviderConfiguration.is_active == 1)  # SQLite stores boolean as 1/0
                .all()
            )
            logger.info(f"Found {len(active_configs)} active provider configurations")

            if not active_configs:
                logger.warning("No active provider configurations found")
                return {}

        except Exception as e:
            logger.error(f"Error querying provider configurations: {e}")
            return {}

        # Try each provider until we get results
        response_times = []  # Track response times for metrics
        successful_provider_name = None

        for config in active_configs:
            try:
                provider_name = config.provider_name
                logger.info(f"Fetching {len(symbols)} symbols using adapter: {provider_name}")

                # Get or create adapter instance from registry
                adapter = await self.registry.get_provider_instance(provider_name)
                if not adapter:
                    # Create new instance with config
                    adapter = await self.registry.create_provider_instance(provider_name, config.config_data)
                    if not adapter:
                        logger.warning(f"No adapter instance available for {provider_name}")
                        continue

                # Use bulk fetch if supported
                if adapter.capabilities.supports_bulk_quotes and len(symbols) > 1:
                    response = await adapter.fetch_prices(symbols)
                    if response.success and response.data:
                        # Collect response time for metrics
                        if response.response_time_ms:
                            response_times.append(response.response_time_ms)

                        # Process bulk results - data should be a dict with symbol keys
                        for symbol in symbols:
                            if symbol in response.data:
                                quote_data = response.data[symbol]

                                # Convert adapter response to legacy format
                                price_data = self._convert_adapter_response(quote_data, symbol, provider_name)
                                if price_data:
                                    results[symbol] = price_data
                                    # Store to database
                                    self._store_price_to_master(symbol, price_data, provider_name)

                        successful_provider_name = provider_name
                        logger.info(f"Bulk fetch successful: {len(results)}/{len(symbols)} symbols")
                        break  # Success, don't try other providers

                else:
                    # Fall back to individual fetches
                    for symbol in symbols:
                        try:
                            response = await adapter.fetch_prices([symbol])
                            if response.success and response.data:
                                # Collect response time for metrics
                                if response.response_time_ms:
                                    response_times.append(response.response_time_ms)

                                # Extract the actual data for this symbol from response.data dict
                                if symbol in response.data:
                                    symbol_data = response.data[symbol]
                                    # Convert adapter response to legacy format
                                    price_data = self._convert_adapter_response(
                                        symbol_data, symbol, provider_name
                                    )
                                    if price_data:
                                        results[symbol] = price_data
                                        # Store to database
                                        self._store_price_to_master(symbol, price_data, provider_name)

                        except Exception as e:
                            logger.error(f"Failed to fetch {symbol} from {provider_name}: {e}")

                    if results:
                        successful_provider_name = provider_name
                        logger.info(f"Individual fetches successful: {len(results)}/{len(symbols)} symbols")
                        break  # Success, don't try other providers

            except Exception as e:
                logger.error(f"Provider {config.provider_name} failed: {e}")
                continue

        # Adapter metrics are now handled by the adapters themselves
        # No need to create duplicate metrics here

        # Queue portfolio updates for all symbols that were updated
        if results:
            self._queue_portfolio_updates(list(results.keys()))

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
            # Debug logging to trace data format
            logger.info(f"Converting adapter data for {symbol}: {list(adapter_data.keys()) if adapter_data else 'None'}")

            # Handle different adapter response formats
            if 'price' in adapter_data:
                price = adapter_data['price']
                logger.info(f"Found 'price' field for {symbol}: {price}")
            elif 'regularMarketPrice' in adapter_data:
                price = adapter_data['regularMarketPrice']
                logger.info(f"Found 'regularMarketPrice' field for {symbol}: {price}")
            elif 'last' in adapter_data:
                price = adapter_data['last']
                logger.info(f"Found 'last' field for {symbol}: {price}")
            else:
                logger.warning(f"No price field found in adapter data for {symbol}. Available fields: {list(adapter_data.keys()) if adapter_data else 'None'}")
                return None

            # Build comprehensive legacy format response with all market data
            response = {
                'symbol': symbol,
                'price': float(price),
                'open': adapter_data.get('open', adapter_data.get('regularMarketOpen')),
                'high': adapter_data.get('high', adapter_data.get('regularMarketDayHigh')),
                'low': adapter_data.get('low', adapter_data.get('regularMarketDayLow')),
                'volume': adapter_data.get('volume', adapter_data.get('regularMarketVolume')),
                'market_cap': adapter_data.get('market_cap', adapter_data.get('marketCap')),
                'company_name': adapter_data.get('company_name', adapter_data.get('longName', adapter_data.get('shortName'))),
                'currency': adapter_data.get('currency', 'USD'),
                'exchange': adapter_data.get('exchange'),
                'change': adapter_data.get('change', 0.0),
                'change_percent': adapter_data.get('change_percent', 0.0),
                'source_timestamp': utc_now().replace(tzinfo=None),
                'provider': provider_name
            }

            logger.info(f"Built response for {symbol}: price={response['price']}, company={response['company_name']}, exchange={response['exchange']}")
            return response

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

            # Validate price data first and track invalid data metrics
            price = price_data.get('price')
            if price is None or str(price).lower() in ['nan', 'inf', '-inf']:
                logger.warning(f"Invalid price data for {symbol}: {price}")

                # Log invalid data metrics
                self._log_invalid_data_metrics(symbol, price, provider_name, "invalid_price")
                return

            # Get provider_id from provider_name by querying the database
            from uuid import UUID
            provider_config = (
                self.db.query(ProviderConfiguration)
                .filter(ProviderConfiguration.provider_name == provider_name)
                .filter(ProviderConfiguration.is_active == True)
                .first()
            )

            if not provider_config:
                logger.error(f"No active provider configuration found for: {provider_name}")
                return

            provider_id = UUID(provider_config.id)

            # Update or create master record
            master_record = self.db.query(RealtimeSymbol).filter(
                RealtimeSymbol.symbol == symbol
            ).first()

            # Safe decimal conversion function
            def safe_decimal(value):
                """Safely convert value to Decimal, returning None for invalid values."""
                if value is None:
                    return None
                try:
                    decimal_val = Decimal(str(value))
                    if decimal_val.is_nan() or decimal_val.is_infinite():
                        return None
                    return decimal_val
                except (ValueError, TypeError, decimal.InvalidOperation):
                    return None

            safe_price = safe_decimal(price_data['price'])
            if safe_price is None:
                logger.warning(f"Could not convert price to valid decimal for {symbol}")
                return

            if master_record:
                # Update existing record
                master_record.current_price = safe_price
                master_record.last_updated = now
                master_record.updated_at = now
                master_record.volume = price_data.get('volume')
                master_record.market_cap = price_data.get('market_cap')
                master_record.company_name = price_data.get('company_name')
                master_record.provider_id = provider_id
            else:
                # Create new record
                master_record = RealtimeSymbol(
                    symbol=symbol,
                    current_price=safe_price,
                    last_updated=now,
                    created_at=now,
                    updated_at=now,
                    volume=price_data.get('volume'),
                    market_cap=price_data.get('market_cap'),
                    company_name=price_data.get('company_name'),
                    provider_id=provider_id
                )
                self.db.add(master_record)

            # Store historical record with safe decimal conversion
            history_record = RealtimePriceHistory(
                symbol=symbol,
                price=safe_decimal(price_data['price']),
                fetched_at=now,
                opening_price=safe_decimal(price_data.get('open')),
                high_price=safe_decimal(price_data.get('high')),
                low_price=safe_decimal(price_data.get('low')),
                volume=price_data.get('volume'),
                provider_id=provider_id,
                source_timestamp=now  # Add required source_timestamp field
            )
            self.db.add(history_record)

            self.db.commit()
            logger.debug(f"Stored price data for {symbol}: ${price_data['price']}")

        except Exception as e:
            logger.error(f"Failed to store price data for {symbol}: {e}")
            self.db.rollback()

    # REMOVED: _log_usage_metrics method - using single adapter metrics path only
    # All metrics are now handled by adapters themselves via ProviderMetricsCollector

    # REMOVED: _log_invalid_data_metrics method - using single adapter metrics path only
    # Invalid data tracking is now handled by adapters themselves via ProviderMetricsCollector

    def _queue_portfolio_updates(self, symbols: List[str]):
        """
        Queue portfolio updates for symbols that have been updated with fresh market data.

        Args:
            symbols: List of stock symbols that were just updated
        """
        try:
            from src.services.portfolio_update_queue import get_portfolio_update_queue

            # Get the portfolio update queue instance
            queue = get_portfolio_update_queue()

            # Find all unique portfolios that contain any of these symbols
            from src.models.portfolio import Portfolio
            from src.models.holding import Holding
            from src.models.stock import Stock
            from sqlalchemy import and_

            affected_portfolios = self.db.query(Portfolio.id).join(Holding).join(Stock).filter(
                and_(
                    Stock.symbol.in_(symbols),
                    Holding.quantity > 0,  # Only active holdings
                    Portfolio.is_active.is_(True)  # Only active portfolios
                )
            ).distinct().all()

            # Queue updates for each affected portfolio
            queued_count = 0
            for portfolio_row in affected_portfolios:
                portfolio_id = str(portfolio_row.id)
                success = queue.queue_portfolio_update(
                    portfolio_id=portfolio_id,
                    symbols=symbols,
                    priority=1  # Normal priority for automatic updates
                )
                if success:
                    queued_count += 1

            if queued_count > 0:
                logger.info(f"Queued portfolio updates for {queued_count} portfolios affected by symbols: {symbols}")
            else:
                logger.debug(f"No portfolios found to update for symbols: {symbols}")

        except Exception as e:
            logger.error(f"Failed to queue portfolio updates for symbols {symbols}: {e}")

    def get_current_price_from_master(self, symbol: str) -> Optional[Dict]:
        """
        Get current price for symbol from master realtime_symbols table.
        Used by transaction validation and API endpoints.
        """
        try:
            master_record = self.db.query(RealtimeSymbol).filter(
                RealtimeSymbol.symbol == symbol
            ).first()

            if not master_record:
                return None

            return {
                "symbol": symbol,
                "price": float(master_record.current_price),
                "fetched_at": master_record.last_updated,
                "volume": master_record.volume,
                "market_cap": master_record.market_cap,
                "company_name": master_record.company_name
            }

        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def get_enabled_providers(self) -> List:
        """Get list of enabled provider configurations."""
        try:
            return (
                self.db.query(ProviderConfiguration)
                .filter(ProviderConfiguration.is_active == 1)  # SQLite stores boolean as 1/0
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get enabled providers: {e}")
            return []

    async def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch price for a single symbol directly from provider.
        Used for transaction validation when symbol is not in local database.
        """
        try:
            # First check if symbol exists in master table
            existing_price = self.get_current_price_from_master(symbol)
            if existing_price:
                return existing_price

            # If not found locally, fetch directly from provider
            logger.info(f"Fetching {symbol} directly from provider for transaction validation")
            result = await self.fetch_multiple_prices([symbol])

            if result and symbol in result:
                return result[symbol]

            return None

        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None


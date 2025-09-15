"""
Real-time portfolio update service.

Handles automatic portfolio recalculation when market data changes.
Calculates daily changes and trends based on opening prices.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from src.core.logging import LoggerMixin
from src.models import Portfolio, Holding, Stock, RealtimePriceHistory
from src.services.dynamic_portfolio_service import DynamicPortfolioService, PortfolioValue
from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService


class RealTimePortfolioService(LoggerMixin):
    """Service for real-time portfolio updates triggered by market data changes."""

    def __init__(self, db: Session):
        self.db = db
        self.dynamic_service = DynamicPortfolioService(db)
        self.metrics_service = PortfolioUpdateMetricsService(db)

    def update_portfolios_for_symbol(self, symbol: str) -> List[Portfolio]:
        """
        Update all portfolios that contain the given symbol.

        Args:
            symbol: Stock symbol that changed

        Returns:
            List of portfolios that were updated
        """
        try:
            self.log_info(f"Updating portfolios for symbol: {symbol}")

            # Find all portfolios containing this symbol
            affected_portfolios = self._find_portfolios_with_symbol(symbol)

            if not affected_portfolios:
                self.log_info(f"No portfolios found with symbol {symbol}")
                return []

            # Get latest price data for the symbol
            latest_price = self._get_latest_price_data(symbol)
            if not latest_price:
                self.log_warning(f"No price data found for symbol {symbol}")
                return []

            # Update each affected portfolio
            updated_portfolios = []
            for portfolio in affected_portfolios:
                if self._update_single_portfolio(portfolio, symbol, latest_price):
                    updated_portfolios.append(portfolio)

            self.log_info(f"Updated {len(updated_portfolios)} portfolios for symbol {symbol}")
            return updated_portfolios

        except Exception as e:
            self.log_error(f"Error updating portfolios for symbol {symbol}", error=str(e))
            return []

    def bulk_update_portfolios_for_symbols(self, symbols: List[str]) -> List[Portfolio]:
        """
        Efficiently update portfolios for multiple symbols.

        Args:
            symbols: List of stock symbols that changed

        Returns:
            List of unique portfolios that were updated
        """
        try:
            self.log_info(f"Bulk updating portfolios for {len(symbols)} symbols")

            # Find all unique portfolios affected by any of these symbols
            all_affected_portfolios = set()
            symbol_price_data = {}

            # Collect price data for all symbols
            for symbol in symbols:
                latest_price = self._get_latest_price_data(symbol)
                if latest_price:
                    symbol_price_data[symbol] = latest_price
                    portfolios = self._find_portfolios_with_symbol(symbol)
                    all_affected_portfolios.update(portfolios)

            if not all_affected_portfolios:
                self.log_info("No portfolios found for any of the symbols")
                return []

            # Update each unique portfolio once
            updated_portfolios = []
            for portfolio in all_affected_portfolios:
                if self._update_portfolio_with_all_holdings(portfolio, symbol_price_data):
                    updated_portfolios.append(portfolio)

            self.log_info(f"Bulk updated {len(updated_portfolios)} unique portfolios")
            return updated_portfolios

        except Exception as e:
            self.log_error(f"Error in bulk portfolio update", error=str(e))
            return []

    def _find_portfolios_with_symbol(self, symbol: str) -> List[Portfolio]:
        """Find all portfolios that have holdings in the given symbol."""
        try:
            portfolios = self.db.query(Portfolio).join(Holding).join(Stock).filter(
                and_(
                    Stock.symbol == symbol,
                    Holding.quantity > 0,  # Only active holdings
                    Portfolio.is_active.is_(True)  # Only active portfolios
                )
            ).distinct().all()

            return portfolios

        except Exception as e:
            self.log_error(f"Error finding portfolios with symbol {symbol}", error=str(e))
            return []

    def _get_latest_price_data(self, symbol: str) -> Optional[RealtimePriceHistory]:
        """Get the most recent price data for a symbol."""
        try:
            latest_price = self.db.query(RealtimePriceHistory).filter(
                RealtimePriceHistory.symbol == symbol
            ).order_by(desc(RealtimePriceHistory.fetched_at)).first()

            return latest_price

        except Exception as e:
            self.log_error(f"Error getting latest price for symbol {symbol}", error=str(e))
            return None

    def _update_single_portfolio(self, portfolio: Portfolio, symbol: str, price_data: RealtimePriceHistory) -> bool:
        """
        Update a single portfolio based on one symbol's price change.
        Recalculates the entire portfolio, not just incremental changes.

        Args:
            portfolio: Portfolio to update
            symbol: Symbol that changed
            price_data: Latest price data for the symbol

        Returns:
            True if portfolio was updated successfully
        """
        start_time = datetime.utcnow()
        processing_start = datetime.utcnow()

        try:
            # Calculate new portfolio values using dynamic service
            portfolio_value = self.dynamic_service.calculate_portfolio_value(
                portfolio.id, use_cache=False
            )

            # Calculate total daily change for all holdings in this portfolio
            # (not just the one symbol that changed)
            total_daily_change = self._calculate_total_daily_change_for_portfolio(portfolio.id)

            # Update portfolio in database
            portfolio.total_value = portfolio_value.total_value
            portfolio.daily_change = total_daily_change

            # Calculate daily change percentage
            if total_daily_change != 0 and portfolio_value.total_value > 0:
                # Opening portfolio value = current value - daily change
                opening_value = portfolio_value.total_value - total_daily_change
                if opening_value > 0:
                    portfolio.daily_change_percent = round(
                        (total_daily_change / opening_value) * 100, 2
                    )
                else:
                    portfolio.daily_change_percent = Decimal("0.00")
            else:
                portfolio.daily_change_percent = Decimal("0.00")

            portfolio.updated_at = datetime.utcnow()
            self.db.commit()

            # Record successful update metrics
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            self.metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=[symbol],
                update_duration_ms=duration_ms,
                status="success",
                trigger_type="market_data_change",
                update_source="automated",
                price_change_timestamp=price_data.fetched_at if price_data else None,
                processing_start_timestamp=processing_start
            )

            self.log_debug(f"Updated portfolio {portfolio.id}: value={portfolio_value.total_value}, "
                          f"change={total_daily_change}, change%={portfolio.daily_change_percent}")

            return True

        except Exception as e:
            # Record failed update metrics
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            self.metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=[symbol],
                update_duration_ms=duration_ms,
                status="error",
                trigger_type="market_data_change",
                update_source="automated",
                error_message=str(e),
                error_type="portfolio_update_error",
                price_change_timestamp=price_data.fetched_at if price_data else None,
                processing_start_timestamp=processing_start
            )

            self.log_error(f"Error updating portfolio {portfolio.id} for symbol {symbol}", error=str(e))
            self.db.rollback()
            return False

    def _update_portfolio_with_all_holdings(self, portfolio: Portfolio, symbol_price_data: Dict[str, RealtimePriceHistory]) -> bool:
        """
        Update a portfolio by recalculating all holdings at once.
        More efficient than updating symbol by symbol.

        Args:
            portfolio: Portfolio to update
            symbol_price_data: Dict mapping symbols to their latest price data

        Returns:
            True if portfolio was updated successfully
        """
        start_time = datetime.utcnow()
        processing_start = datetime.utcnow()

        try:
            # Calculate new portfolio values using dynamic service
            portfolio_value = self.dynamic_service.calculate_portfolio_value(
                portfolio.id, use_cache=False
            )

            # Calculate total daily change for all holdings in this portfolio
            total_daily_change = self._calculate_total_daily_change(
                portfolio.id, symbol_price_data
            )

            # Update portfolio in database
            portfolio.total_value = portfolio_value.total_value
            portfolio.daily_change = total_daily_change

            # Calculate daily change percentage
            if total_daily_change != 0 and portfolio_value.total_value > 0:
                # Opening portfolio value = current value - daily change
                opening_value = portfolio_value.total_value - total_daily_change
                if opening_value > 0:
                    portfolio.daily_change_percent = round(
                        (total_daily_change / opening_value) * 100, 2
                    )
                else:
                    portfolio.daily_change_percent = Decimal("0.00")
            else:
                portfolio.daily_change_percent = Decimal("0.00")

            portfolio.updated_at = datetime.utcnow()
            self.db.commit()

            # Record successful bulk update metrics
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            symbols_list = list(symbol_price_data.keys())

            self.metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=symbols_list,
                update_duration_ms=duration_ms,
                status="success",
                trigger_type="bulk_market_data",
                update_source="automated",
                coalesced_count=len(symbols_list),  # Number of symbols processed together
                processing_start_timestamp=processing_start
            )

            self.log_debug(f"Bulk updated portfolio {portfolio.id}: value={portfolio_value.total_value}, "
                          f"change={total_daily_change}, change%={portfolio.daily_change_percent}")

            return True

        except Exception as e:
            # Record failed bulk update metrics
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            symbols_list = list(symbol_price_data.keys())

            self.metrics_service.record_portfolio_update(
                portfolio_id=str(portfolio.id),
                symbols_updated=symbols_list,
                update_duration_ms=duration_ms,
                status="error",
                trigger_type="bulk_market_data",
                update_source="automated",
                error_message=str(e),
                error_type="bulk_portfolio_update_error",
                coalesced_count=len(symbols_list),
                processing_start_timestamp=processing_start
            )

            self.log_error(f"Error bulk updating portfolio {portfolio.id}", error=str(e))
            self.db.rollback()
            return False

    def _calculate_daily_change_for_symbol(self, portfolio_id: str, symbol: str, price_data: RealtimePriceHistory) -> Decimal:
        """
        Calculate daily change for a specific symbol within a portfolio.

        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            price_data: Latest price data with opening price

        Returns:
            Daily change amount for this symbol in this portfolio
        """
        try:
            if not price_data.opening_price:
                return Decimal("0.00")

            # Get the holding for this symbol in this portfolio
            holding = self.db.query(Holding).join(Stock).filter(
                and_(
                    Holding.portfolio_id == portfolio_id,
                    Stock.symbol == symbol,
                    Holding.quantity > 0
                )
            ).first()

            if not holding:
                return Decimal("0.00")

            # Daily change = (current_price - opening_price) * quantity
            price_change_per_share = price_data.price - price_data.opening_price
            total_change = price_change_per_share * holding.quantity

            return total_change

        except Exception as e:
            self.log_error(f"Error calculating daily change for {symbol} in portfolio {portfolio_id}", error=str(e))
            return Decimal("0.00")

    def _calculate_total_daily_change_for_portfolio(self, portfolio_id: str) -> Decimal:
        """
        Calculate total daily change for all holdings in a portfolio.
        Gets latest price data for each symbol in the portfolio.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Total daily change for the entire portfolio
        """
        try:
            total_change = Decimal("0.00")

            # Get all holdings in this portfolio
            holdings = self.db.query(Holding).options(
                joinedload(Holding.stock)
            ).filter(
                and_(
                    Holding.portfolio_id == portfolio_id,
                    Holding.quantity > 0
                )
            ).all()

            # Calculate daily change for each holding
            for holding in holdings:
                symbol = holding.stock.symbol

                # Get latest price data for this symbol
                price_data = self._get_latest_price_data(symbol)

                if price_data and price_data.opening_price:
                    price_change_per_share = price_data.price - price_data.opening_price
                    holding_change = price_change_per_share * holding.quantity
                    total_change += holding_change

            return total_change

        except Exception as e:
            self.log_error(f"Error calculating total daily change for portfolio {portfolio_id}", error=str(e))
            return Decimal("0.00")

    def _calculate_total_daily_change(self, portfolio_id: str, symbol_price_data: Dict[str, RealtimePriceHistory]) -> Decimal:
        """
        Calculate total daily change for all holdings in a portfolio using provided price data.

        Args:
            portfolio_id: Portfolio ID
            symbol_price_data: Dict mapping symbols to their latest price data

        Returns:
            Total daily change for the entire portfolio
        """
        try:
            total_change = Decimal("0.00")

            # Get all holdings in this portfolio
            holdings = self.db.query(Holding).options(
                joinedload(Holding.stock)
            ).filter(
                and_(
                    Holding.portfolio_id == portfolio_id,
                    Holding.quantity > 0
                )
            ).all()

            # Calculate daily change for each holding
            for holding in holdings:
                symbol = holding.stock.symbol
                price_data = symbol_price_data.get(symbol)

                if price_data and price_data.opening_price:
                    price_change_per_share = price_data.price - price_data.opening_price
                    holding_change = price_change_per_share * holding.quantity
                    total_change += holding_change

            return total_change

        except Exception as e:
            self.log_error(f"Error calculating total daily change for portfolio {portfolio_id}", error=str(e))
            return Decimal("0.00")
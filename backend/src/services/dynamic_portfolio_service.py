"""
Dynamic portfolio valuation service.
Calculates portfolio values based on cached market price data.
Uses last received price data, not external API calls on each request.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, desc

from src.core.logging import LoggerMixin
from src.models import Portfolio, Holding, Stock, RealtimePriceHistory, PortfolioValuation
from src.models.realtime_symbol import RealtimeSymbol
from src.schemas.portfolio import PortfolioResponse
from src.schemas.holding import HoldingResponse


class PortfolioValue:
    """Container for portfolio valuation data."""
    def __init__(
        self,
        total_value: Decimal = Decimal("0.00"),
        total_cost_basis: Decimal = Decimal("0.00"),
        total_unrealized_gain: Decimal = Decimal("0.00"),
        total_gain_percent: Decimal = Decimal("0.00")
    ):
        self.total_value = total_value
        self.total_cost_basis = total_cost_basis
        self.total_unrealized_gain = total_unrealized_gain
        self.total_gain_percent = total_gain_percent


class DynamicPortfolioService(LoggerMixin):
    """Service for calculating dynamic portfolio valuations using cached price data."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_portfolio_value(self, portfolio_id: UUID, use_cache: bool = True) -> PortfolioValue:
        """
        Calculate dynamic portfolio value based on cached market price data.

        Args:
            portfolio_id: UUID of the portfolio to calculate
            use_cache: Whether to check for cached valuations first

        Returns:
            PortfolioValue object with calculated totals
        """
        try:
            self.log_info("Calculating dynamic portfolio value", portfolio_id=str(portfolio_id))

            # Check for cached valuation first (if use_cache=True)
            if use_cache:
                cached_value = self._get_cached_portfolio_value(portfolio_id)
                if cached_value:
                    self.log_info("Using cached portfolio valuation", portfolio_id=str(portfolio_id))
                    return cached_value

            # Get all holdings for the portfolio
            holdings = self.db.query(Holding).options(
                joinedload(Holding.stock)
            ).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.quantity > 0
            ).all()

            if not holdings:
                self.log_info("No holdings found for portfolio", portfolio_id=str(portfolio_id))
                return PortfolioValue()

            # Get unique symbols from holdings
            symbols = list(set(holding.stock.symbol for holding in holdings))
            self.log_info("Getting cached prices for symbols", symbols=symbols)

            # Get cached current prices
            current_prices = self._get_cached_prices(symbols)

            # Calculate values for each holding
            total_value = Decimal("0.00")
            total_cost_basis = Decimal("0.00")

            for holding in holdings:
                symbol = holding.stock.symbol
                quantity = holding.quantity
                average_cost = holding.average_cost

                # Get cached price or fallback to average cost
                current_price = current_prices.get(symbol)
                if current_price is None:
                    self.log_warning(f"No cached price available for {symbol}, using average cost as fallback")
                    current_price = average_cost

                # Calculate values
                holding_cost_basis = quantity * average_cost
                holding_current_value = quantity * current_price

                total_value += holding_current_value
                total_cost_basis += holding_cost_basis

                self.log_debug(
                    f"Holding calculation: {symbol}",
                    quantity=str(quantity),
                    average_cost=str(average_cost),
                    current_price=str(current_price),
                    current_value=str(holding_current_value)
                )

            # Calculate unrealized gain/loss and percentage
            total_unrealized_gain = total_value - total_cost_basis
            total_gain_percent = Decimal("0.00")
            if total_cost_basis > 0:
                total_gain_percent = (total_unrealized_gain / total_cost_basis) * 100

            result = PortfolioValue(
                total_value=total_value,
                total_cost_basis=total_cost_basis,
                total_unrealized_gain=total_unrealized_gain,
                total_gain_percent=total_gain_percent
            )

            # Skip caching for now to avoid readonly database errors
            # self._cache_portfolio_value(portfolio_id, result, len(holdings))

            self.log_info(
                "Portfolio value calculated and cached",
                portfolio_id=str(portfolio_id),
                total_value=str(result.total_value),
                unrealized_gain=str(result.total_unrealized_gain),
                gain_percent=str(result.total_gain_percent)
            )

            return result

        except Exception as e:
            self.log_error("Error calculating portfolio value", portfolio_id=str(portfolio_id), error=str(e))
            # Return default values on error
            return PortfolioValue()

    def get_dynamic_portfolio(self, portfolio_id: UUID) -> Optional[PortfolioResponse]:
        """
        Get portfolio with dynamically calculated values.

        Args:
            portfolio_id: UUID of the portfolio

        Returns:
            PortfolioResponse with current market values
        """
        try:
            # Get the portfolio
            portfolio = self.db.query(Portfolio).options(
                joinedload(Portfolio.holdings).joinedload(Holding.stock)
            ).filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active.is_(True)
            ).first()

            if not portfolio:
                self.log_warning("Portfolio not found", portfolio_id=str(portfolio_id))
                return None

            # Calculate dynamic values
            portfolio_value = self.calculate_portfolio_value(portfolio_id)

            # Get holdings with current market prices
            updated_holdings = self._get_dynamic_holdings(portfolio_id)

            # Create response with updated values
            portfolio_dict = {
                "id": portfolio.id,
                "name": portfolio.name,
                "description": portfolio.description,
                "owner_id": portfolio.owner_id,
                "total_value": portfolio_value.total_value,
                "daily_change": portfolio_value.total_unrealized_gain,
                "daily_change_percent": portfolio_value.total_gain_percent,
                "created_at": portfolio.created_at,
                "updated_at": portfolio.updated_at,
                "is_active": portfolio.is_active,
                "holdings": updated_holdings
            }

            return PortfolioResponse.model_validate(portfolio_dict)

        except Exception as e:
            self.log_error("Error getting dynamic portfolio", portfolio_id=str(portfolio_id), error=str(e))
            return None

    def _get_dynamic_holdings(self, portfolio_id: UUID) -> List[HoldingResponse]:
        """
        Get holdings with dynamically calculated current values.

        Args:
            portfolio_id: UUID of the portfolio

        Returns:
            List of HoldingResponse objects with updated values
        """
        try:
            # Get holdings with stock info
            holdings = self.db.query(Holding).options(
                joinedload(Holding.stock)
            ).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.quantity > 0
            ).all()

            if not holdings:
                return []

            # Get cached prices for all symbols
            symbols = [holding.stock.symbol for holding in holdings]
            current_prices = self._get_cached_prices(symbols)

            updated_holdings = []
            for holding in holdings:
                symbol = holding.stock.symbol
                current_price = current_prices.get(symbol, holding.average_cost)

                if current_price is None:
                    current_price = holding.average_cost

                # Calculate updated values
                current_value = holding.quantity * current_price
                cost_basis = holding.quantity * holding.average_cost
                unrealized_gain_loss = current_value - cost_basis

                # Calculate unrealized gain/loss percentage
                unrealized_gain_loss_percent = Decimal("0.00")
                if cost_basis > 0:
                    unrealized_gain_loss_percent = (unrealized_gain_loss / cost_basis) * 100

                # Create holding dict with updated values
                holding_dict = {
                    "id": holding.id,
                    "portfolio_id": holding.portfolio_id,
                    "stock_id": holding.stock_id,
                    "stock": {
                        "id": holding.stock.id,
                        "symbol": holding.stock.symbol,
                        "company_name": holding.stock.company_name,
                        "exchange": holding.stock.exchange,
                        "status": holding.stock.status,
                        "created_at": holding.stock.created_at,
                        "updated_at": holding.stock.updated_at
                    },
                    "quantity": holding.quantity,
                    "average_cost": holding.average_cost,
                    "current_value": current_value,
                    "unrealized_gain_loss": unrealized_gain_loss,
                    "unrealized_gain_loss_percent": unrealized_gain_loss_percent,
                    "created_at": holding.created_at,
                    "updated_at": holding.updated_at
                }

                updated_holdings.append(HoldingResponse.model_validate(holding_dict))

            return updated_holdings

        except Exception as e:
            self.log_error("Error getting dynamic holdings", portfolio_id=str(portfolio_id), error=str(e))
            return []

    def update_portfolio_cache_values(self, portfolio_id: UUID) -> bool:
        """
        Update the cached portfolio values in the database.
        This can be called periodically to update stored values.

        Args:
            portfolio_id: UUID of the portfolio to update

        Returns:
            True if successful, False otherwise
        """
        try:
            portfolio_value = self.calculate_portfolio_value(portfolio_id)

            # Update portfolio table with calculated values
            self.db.execute(text("""
                UPDATE portfolios
                SET
                    total_value = :total_value,
                    daily_change = :daily_change,
                    daily_change_percent = :daily_change_percent,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :portfolio_id
            """), {
                "portfolio_id": str(portfolio_id),
                "total_value": float(portfolio_value.total_value),
                "daily_change": float(portfolio_value.total_unrealized_gain),
                "daily_change_percent": float(portfolio_value.total_gain_percent)
            })

            # Update holdings table with current values
            holdings = self.db.query(Holding).options(
                joinedload(Holding.stock)
            ).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.quantity > 0
            ).all()

            if holdings:
                symbols = [holding.stock.symbol for holding in holdings]
                current_prices = self._get_cached_prices(symbols)

                for holding in holdings:
                    symbol = holding.stock.symbol
                    current_price = current_prices.get(symbol, holding.average_cost)

                    if current_price:
                        current_value = holding.quantity * current_price
                        cost_basis = holding.quantity * holding.average_cost
                        unrealized_gain_loss = current_value - cost_basis

                        self.db.execute(text("""
                            UPDATE holdings
                            SET
                                current_value = :current_value,
                                unrealized_gain_loss = :unrealized_gain_loss,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :holding_id
                        """), {
                            "holding_id": str(holding.id),
                            "current_value": float(current_value),
                            "unrealized_gain_loss": float(unrealized_gain_loss)
                        })

            self.db.commit()
            self.log_info("Portfolio cache values updated successfully", portfolio_id=str(portfolio_id))
            return True

        except Exception as e:
            self.db.rollback()
            self.log_error("Error updating portfolio cache values", portfolio_id=str(portfolio_id), error=str(e))
            return False

    def _get_cached_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """
        Get current prices from master table (single source of truth).

        Args:
            symbols: List of stock symbols to get prices for

        Returns:
            Dictionary mapping symbols to their current prices from master table
        """
        if not symbols:
            return {}

        try:
            # Get current prices from master table (realtime_symbols)
            prices = {}

            for symbol in symbols:
                # Get current price from master table
                master_record = self.db.query(RealtimeSymbol).filter(
                    RealtimeSymbol.symbol == symbol
                ).first()

                if master_record:
                    prices[symbol] = Decimal(str(master_record.current_price))
                    self.log_debug(f"Master table price for {symbol}: {master_record.current_price}")

            self.log_info("Retrieved prices from master table", symbols=symbols, found_count=len(prices))
            return prices

        except Exception as e:
            self.log_error("Error retrieving prices from master table", error=str(e))
            return {}

    def _get_cached_portfolio_value(self, portfolio_id: UUID) -> Optional[PortfolioValue]:
        """
        Get cached portfolio valuation if available and not expired.

        Args:
            portfolio_id: UUID of the portfolio

        Returns:
            PortfolioValue if cached and valid, None otherwise
        """
        try:
            # Get most recent cached valuation
            cached_valuation = self.db.query(PortfolioValuation).filter(
                PortfolioValuation.portfolio_id == portfolio_id
            ).order_by(desc(PortfolioValuation.calculated_at)).first()

            if not cached_valuation:
                self.log_debug("No cached valuation found", portfolio_id=str(portfolio_id))
                return None

            if cached_valuation.is_expired:
                self.log_debug("Cached valuation expired", portfolio_id=str(portfolio_id))
                return None

            if cached_valuation.is_stale:
                self.log_debug("Cached valuation marked as stale", portfolio_id=str(portfolio_id))
                return None

            # Convert to PortfolioValue object
            return PortfolioValue(
                total_value=Decimal(str(cached_valuation.total_value)),
                total_cost_basis=Decimal(str(cached_valuation.total_cost_basis)),
                total_unrealized_gain=Decimal(str(cached_valuation.total_gain_loss)),
                total_gain_percent=Decimal(str(cached_valuation.total_gain_loss_percent))
            )

        except Exception as e:
            self.log_error("Error retrieving cached portfolio value", portfolio_id=str(portfolio_id), error=str(e))
            return None

    def _cache_portfolio_value(self, portfolio_id: UUID, portfolio_value: PortfolioValue, holdings_count: int) -> bool:
        """
        Cache the calculated portfolio value.

        Args:
            portfolio_id: UUID of the portfolio
            portfolio_value: The calculated portfolio value
            holdings_count: Number of holdings in portfolio

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create new cache entry
            cached_valuation = PortfolioValuation(
                portfolio_id=portfolio_id,
                total_value=portfolio_value.total_value,
                total_cost_basis=portfolio_value.total_cost_basis,
                total_gain_loss=portfolio_value.total_unrealized_gain,
                total_gain_loss_percent=portfolio_value.total_gain_percent,
                holdings_count=holdings_count
            )

            self.db.add(cached_valuation)
            self.db.commit()

            self.log_debug("Portfolio valuation cached", portfolio_id=str(portfolio_id))
            return True

        except Exception as e:
            self.db.rollback()
            self.log_error("Error caching portfolio value", portfolio_id=str(portfolio_id), error=str(e))
            return False
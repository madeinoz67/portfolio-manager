"""
Admin dashboard service for aggregating system metrics.

Provides methods for calculating pricing metrics and system statistics
using the master table as the single source of truth.
"""

from typing import Dict, List, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.logging import LoggerMixin
from src.models.realtime_symbol import RealtimeSymbol


class AdminDashboardService(LoggerMixin):
    """Service for admin dashboard metrics and system statistics."""

    def __init__(self, db: Session):
        self.db = db

    def get_pricing_metrics(self) -> Dict[str, Any]:
        """
        Get pricing metrics from the master table.

        Returns:
            Dictionary containing pricing statistics calculated from the realtime_symbols table
        """
        self.log_info("Calculating pricing metrics from master table")

        try:
            # Get all symbols from master table
            symbols = self.db.query(RealtimeSymbol).all()

            if not symbols:
                self.log_info("No symbols found in master table")
                return {
                    "total_symbols": 0,
                    "avg_price": Decimal("0.00"),
                    "symbol_prices": {}
                }

            # Calculate total symbols
            total_symbols = len(symbols)

            # Calculate average price
            total_price = sum(symbol.current_price for symbol in symbols)
            avg_price = total_price / total_symbols if total_symbols > 0 else Decimal("0.00")

            # Build symbol prices dictionary
            symbol_prices = {
                symbol.symbol: symbol.current_price for symbol in symbols
            }

            metrics = {
                "total_symbols": total_symbols,
                "avg_price": avg_price,
                "symbol_prices": symbol_prices
            }

            self.log_info(
                "Pricing metrics calculated from master table",
                total_symbols=total_symbols,
                avg_price=str(avg_price)
            )

            return metrics

        except Exception as e:
            self.log_error("Error calculating pricing metrics", error=str(e))
            # Return default values on error
            return {
                "total_symbols": 0,
                "avg_price": Decimal("0.00"),
                "symbol_prices": {}
            }
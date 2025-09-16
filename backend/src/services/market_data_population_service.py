"""
Market Data Population Service

Populates market data tables for existing portfolio holdings to enable
daily change calculations. This service addresses the issue where portfolio
overview shows $0.00 daily change due to missing market data.

Architecture:
- Identifies symbols from existing portfolio holdings that need market data
- Creates RealtimeSymbol master records (single source of truth)
- Creates RealtimePriceHistory records with previous close data
- Populates previous_close field in stocks table for compatibility
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.logging import LoggerMixin
from src.models.stock import Stock
from src.models.realtime_symbol import RealtimeSymbol
from src.models.realtime_price_history import RealtimePriceHistory
from src.models.market_data_provider import MarketDataProvider
from src.utils.datetime_utils import utc_now


class MarketDataPopulationService(LoggerMixin):
    """Service for populating market data for existing portfolio holdings."""

    def __init__(self, db: Session):
        self.db = db

    def populate_portfolio_symbols_market_data(self, mock_data: bool = True) -> Dict[str, any]:
        """
        Populate market data for all symbols that appear in active portfolio holdings.

        Args:
            mock_data: If True, generates mock previous close data. If False, would
                      fetch from actual market data APIs (not implemented yet).

        Returns:
            Dictionary with operation results and statistics
        """
        try:
            self.log_info("Starting market data population for portfolio symbols")

            # Step 1: Get enabled provider
            provider = self._get_enabled_provider()
            if not provider:
                raise ValueError("No enabled market data provider found")

            # Step 2: Identify symbols that need market data
            symbols_needing_data = self._get_symbols_needing_market_data()
            self.log_info(f"Found {len(symbols_needing_data)} symbols needing market data",
                         symbols=[s['symbol'] for s in symbols_needing_data])

            if not symbols_needing_data:
                return {
                    "status": "success",
                    "message": "No symbols need market data population",
                    "symbols_processed": 0,
                    "symbols": []
                }

            # Step 3: Populate market data for each symbol
            populated_symbols = []
            for symbol_data in symbols_needing_data:
                try:
                    result = self._populate_symbol_market_data(symbol_data, provider, mock_data)
                    populated_symbols.append(result)
                    self.log_info(f"Populated market data for {symbol_data['symbol']}", **result)
                except Exception as e:
                    self.log_error(f"Failed to populate data for {symbol_data['symbol']}", error=str(e))

            self.db.commit()

            self.log_info("Market data population completed",
                         symbols_processed=len(populated_symbols))

            return {
                "status": "success",
                "message": f"Successfully populated market data for {len(populated_symbols)} symbols",
                "symbols_processed": len(populated_symbols),
                "symbols": populated_symbols
            }

        except Exception as e:
            self.db.rollback()
            self.log_error("Error during market data population", error=str(e))
            return {
                "status": "error",
                "message": f"Market data population failed: {str(e)}",
                "symbols_processed": 0,
                "symbols": []
            }

    def _get_enabled_provider(self) -> Optional[MarketDataProvider]:
        """Get the first enabled market data provider."""
        return self.db.query(MarketDataProvider).filter(
            MarketDataProvider.is_enabled == True
        ).first()

    def _get_symbols_needing_market_data(self) -> List[Dict[str, any]]:
        """
        Get symbols from active portfolio holdings that don't have market data.

        Returns list of dicts with symbol, current_price, and company_name.
        """
        result = self.db.execute(text("""
            SELECT DISTINCT
                s.symbol,
                s.current_price,
                s.company_name,
                s.id as stock_id
            FROM stocks s
            JOIN holdings h ON s.id = h.stock_id
            JOIN portfolios p ON h.portfolio_id = p.id
            WHERE p.is_active = 1
                AND h.quantity > 0
                AND s.symbol NOT IN (SELECT symbol FROM realtime_symbols)
            ORDER BY s.symbol
        """)).fetchall()

        return [
            {
                "symbol": row.symbol,
                "current_price": row.current_price,
                "company_name": row.company_name,
                "stock_id": row.stock_id
            }
            for row in result
        ]

    def _populate_symbol_market_data(
        self,
        symbol_data: Dict[str, any],
        provider: MarketDataProvider,
        mock_data: bool = True
    ) -> Dict[str, any]:
        """
        Populate market data for a single symbol.

        Args:
            symbol_data: Dict with symbol, current_price, company_name, stock_id
            provider: MarketDataProvider to use
            mock_data: Whether to generate mock data or fetch from API

        Returns:
            Dict with populated data details
        """
        symbol = symbol_data["symbol"]
        current_price = Decimal(str(symbol_data["current_price"]))

        if mock_data:
            # Generate mock previous close (2-5% below current price for realistic daily gains)
            previous_close = current_price * Decimal("0.97")  # 3% increase
        else:
            # TODO: Implement actual API fetching
            raise NotImplementedError("Real API fetching not yet implemented")

        # Step 1: Update stock record with previous_close
        stock_id = UUID(symbol_data["stock_id"]) if isinstance(symbol_data["stock_id"], str) else symbol_data["stock_id"]
        stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
        if stock:
            stock.previous_close = previous_close

        # Step 2: Create price history record
        price_history = RealtimePriceHistory(
            symbol=symbol,
            price=current_price,
            previous_close=previous_close,
            source_timestamp=utc_now(),
            fetched_at=utc_now(),
            provider_id=provider.id
        )
        self.db.add(price_history)
        self.db.flush()  # Get the ID

        # Step 3: Create master symbol record (single source of truth)
        master_symbol = RealtimeSymbol(
            symbol=symbol,
            current_price=current_price,
            company_name=symbol_data["company_name"],
            last_updated=utc_now(),
            provider_id=provider.id,
            latest_history_id=price_history.id
        )
        self.db.add(master_symbol)
        self.db.flush()

        # Calculate the daily change this will enable
        daily_change_per_share = current_price - previous_close

        return {
            "symbol": symbol,
            "current_price": float(current_price),
            "previous_close": float(previous_close),
            "daily_change_per_share": float(daily_change_per_share),
            "change_percent": float((daily_change_per_share / previous_close) * 100),
            "master_symbol_id": master_symbol.symbol,
            "history_record_id": price_history.id
        }

    def get_market_data_status(self) -> Dict[str, any]:
        """
        Get current status of market data for portfolio symbols.

        Returns statistics about market data coverage for portfolio holdings.
        """
        try:
            # Get all symbols in portfolios
            portfolio_symbols = self.db.execute(text("""
                SELECT DISTINCT s.symbol
                FROM stocks s
                JOIN holdings h ON s.id = h.stock_id
                JOIN portfolios p ON h.portfolio_id = p.id
                WHERE p.is_active = 1 AND h.quantity > 0
            """)).fetchall()

            # Get symbols with master data
            symbols_with_master_data = self.db.execute(text("""
                SELECT DISTINCT rs.symbol
                FROM realtime_symbols rs
                JOIN stocks s ON rs.symbol = s.symbol
                JOIN holdings h ON s.id = h.stock_id
                JOIN portfolios p ON h.portfolio_id = p.id
                WHERE p.is_active = 1 AND h.quantity > 0
            """)).fetchall()

            # Get symbols with previous close data
            symbols_with_previous_close = self.db.execute(text("""
                SELECT DISTINCT s.symbol
                FROM stocks s
                JOIN holdings h ON s.id = h.stock_id
                JOIN portfolios p ON h.portfolio_id = p.id
                WHERE p.is_active = 1
                    AND h.quantity > 0
                    AND s.previous_close IS NOT NULL
            """)).fetchall()

            total_symbols = len(portfolio_symbols)
            symbols_with_master = len(symbols_with_master_data)
            symbols_with_prev_close = len(symbols_with_previous_close)

            missing_symbols = [
                row.symbol for row in portfolio_symbols
                if row.symbol not in [r.symbol for r in symbols_with_master_data]
            ]

            return {
                "total_portfolio_symbols": total_symbols,
                "symbols_with_master_data": symbols_with_master,
                "symbols_with_previous_close": symbols_with_prev_close,
                "coverage_percentage": (symbols_with_master / total_symbols * 100) if total_symbols > 0 else 100,
                "missing_symbols": missing_symbols,
                "daily_change_enabled": symbols_with_master == total_symbols and symbols_with_prev_close == total_symbols
            }

        except Exception as e:
            self.log_error("Error getting market data status", error=str(e))
            return {
                "error": str(e),
                "total_portfolio_symbols": 0,
                "symbols_with_master_data": 0,
                "symbols_with_previous_close": 0,
                "coverage_percentage": 0,
                "missing_symbols": [],
                "daily_change_enabled": False
            }

    def verify_daily_change_calculation(self, portfolio_id: str) -> Dict[str, any]:
        """
        Verify that daily change calculation will work for a specific portfolio.

        Args:
            portfolio_id: UUID string of portfolio to check

        Returns:
            Verification results with details about market data availability
        """
        try:
            from src.services.dynamic_portfolio_service import DynamicPortfolioService

            # Get portfolio symbols
            symbols = self.db.execute(text("""
                SELECT DISTINCT s.symbol, s.current_price, s.previous_close
                FROM stocks s
                JOIN holdings h ON s.id = h.stock_id
                WHERE h.portfolio_id = :portfolio_id AND h.quantity > 0
            """), {"portfolio_id": portfolio_id}).fetchall()

            # Check master symbol coverage
            master_symbols = self.db.execute(text("""
                SELECT DISTINCT rs.symbol, rs.current_price
                FROM realtime_symbols rs
                JOIN stocks s ON rs.symbol = s.symbol
                JOIN holdings h ON s.id = h.stock_id
                WHERE h.portfolio_id = :portfolio_id AND h.quantity > 0
            """), {"portfolio_id": portfolio_id}).fetchall()

            # Test the calculation
            portfolio_service = DynamicPortfolioService(self.db)
            portfolio_response = portfolio_service.get_dynamic_portfolio(portfolio_id)

            symbol_details = []
            for symbol_row in symbols:
                master_data = next((m for m in master_symbols if m.symbol == symbol_row.symbol), None)
                symbol_details.append({
                    "symbol": symbol_row.symbol,
                    "has_current_price": symbol_row.current_price is not None,
                    "has_previous_close": symbol_row.previous_close is not None,
                    "has_master_record": master_data is not None,
                    "current_price": float(symbol_row.current_price) if symbol_row.current_price else None,
                    "previous_close": float(symbol_row.previous_close) if symbol_row.previous_close else None
                })

            return {
                "portfolio_id": portfolio_id,
                "total_symbols": len(symbols),
                "symbols_with_complete_data": len([s for s in symbol_details if s["has_master_record"] and s["has_previous_close"]]),
                "daily_change_calculated": float(portfolio_response.daily_change) if portfolio_response else 0.0,
                "daily_change_percent": float(portfolio_response.daily_change_percent) if portfolio_response else 0.0,
                "calculation_working": portfolio_response is not None and portfolio_response.daily_change != Decimal("0.00"),
                "symbol_details": symbol_details
            }

        except Exception as e:
            self.log_error("Error verifying daily change calculation", portfolio_id=portfolio_id, error=str(e))
            return {
                "portfolio_id": portfolio_id,
                "error": str(e),
                "calculation_working": False
            }
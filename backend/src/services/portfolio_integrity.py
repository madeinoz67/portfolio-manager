"""
Portfolio integrity service for ensuring data consistency and preventing discrepancies.
"""

from decimal import Decimal
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.logging import LoggerMixin
from src.models import Portfolio, Holding, Transaction, Stock


class PortfolioIntegrityService(LoggerMixin):
    """Service to ensure portfolio data integrity and consistency."""

    def __init__(self, db: Session):
        self.db = db

    def verify_portfolio_integrity(self, portfolio_id: UUID) -> List[str]:
        """
        Comprehensive integrity check for a portfolio.
        Returns list of issues found (empty list means portfolio is consistent).
        """
        issues = []

        try:
            # Check 1: Portfolio exists and is active
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
            if not portfolio:
                issues.append(f"Portfolio {portfolio_id} not found")
                return issues

            if not portfolio.is_active:
                issues.append(f"Portfolio {portfolio_id} is not active")

            # Check 2: All holdings have valid stock references
            orphaned_holdings = self.db.execute(text("""
                SELECT h.id, h.stock_id
                FROM holdings h
                LEFT JOIN stocks s ON h.stock_id = s.id
                WHERE h.portfolio_id = :portfolio_id AND s.id IS NULL
            """), {"portfolio_id": str(portfolio_id)}).fetchall()

            for holding_id, stock_id in orphaned_holdings:
                issues.append(f"Holding {holding_id} has invalid stock_id {stock_id}")

            # Check 3: All transactions have valid stock references
            orphaned_transactions = self.db.execute(text("""
                SELECT t.id, t.stock_id
                FROM transactions t
                LEFT JOIN stocks s ON t.stock_id = s.id
                WHERE t.portfolio_id = :portfolio_id AND s.id IS NULL
            """), {"portfolio_id": str(portfolio_id)}).fetchall()

            for transaction_id, stock_id in orphaned_transactions:
                issues.append(f"Transaction {transaction_id} has invalid stock_id {stock_id}")

            # Check 4: Holdings quantities match transaction history
            stock_discrepancies = self._check_holdings_vs_transactions(portfolio_id)
            issues.extend(stock_discrepancies)

            # Check 5: Portfolio total_value matches sum of holdings
            total_discrepancy = self._check_portfolio_total_accuracy(portfolio_id)
            if total_discrepancy:
                issues.append(total_discrepancy)

            # Check 6: No negative holdings
            negative_holdings = self.db.execute(text("""
                SELECT h.id, s.symbol, h.quantity
                FROM holdings h
                JOIN stocks s ON h.stock_id = s.id
                WHERE h.portfolio_id = :portfolio_id AND h.quantity < 0
            """), {"portfolio_id": str(portfolio_id)}).fetchall()

            for holding_id, symbol, quantity in negative_holdings:
                issues.append(f"Negative holding: {symbol} quantity {quantity} in holding {holding_id}")

            # Check 7: Holdings with zero quantity should not exist
            zero_holdings = self.db.execute(text("""
                SELECT h.id, s.symbol
                FROM holdings h
                JOIN stocks s ON h.stock_id = s.id
                WHERE h.portfolio_id = :portfolio_id AND h.quantity = 0
            """), {"portfolio_id": str(portfolio_id)}).fetchall()

            for holding_id, symbol in zero_holdings:
                issues.append(f"Zero quantity holding should be deleted: {symbol} in holding {holding_id}")

        except Exception as e:
            self.log_error("Error during integrity check", error=str(e))
            issues.append(f"Integrity check failed: {str(e)}")

        return issues

    def _check_holdings_vs_transactions(self, portfolio_id: UUID) -> List[str]:
        """Check that holdings quantities match transaction history."""
        issues = []

        # Get all stocks in this portfolio
        stock_ids = self.db.execute(text("""
            SELECT DISTINCT stock_id FROM holdings WHERE portfolio_id = :portfolio_id
            UNION
            SELECT DISTINCT stock_id FROM transactions WHERE portfolio_id = :portfolio_id
        """), {"portfolio_id": str(portfolio_id)}).fetchall()

        for (stock_id,) in stock_ids:
            # Calculate quantity from transactions
            transaction_total = self.db.execute(text("""
                SELECT
                    SUM(CASE
                        WHEN transaction_type IN ('BUY', 'TRANSFER_IN', 'BONUS_SHARES') THEN quantity
                        WHEN transaction_type IN ('SELL', 'TRANSFER_OUT') THEN -quantity
                        WHEN transaction_type = 'STOCK_SPLIT' THEN quantity * (price_per_share - 1) -- Assuming price_per_share is split ratio
                        ELSE 0
                    END) as calculated_quantity
                FROM transactions
                WHERE portfolio_id = :portfolio_id AND stock_id = :stock_id
            """), {"portfolio_id": str(portfolio_id), "stock_id": stock_id}).scalar() or Decimal(0)

            # Get holding quantity
            holding_quantity = self.db.execute(text("""
                SELECT quantity FROM holdings
                WHERE portfolio_id = :portfolio_id AND stock_id = :stock_id
            """), {"portfolio_id": str(portfolio_id), "stock_id": stock_id}).scalar() or Decimal(0)

            # Get stock symbol for error reporting
            stock_symbol = self.db.execute(text("""
                SELECT symbol FROM stocks WHERE id = :stock_id
            """), {"stock_id": stock_id}).scalar() or "UNKNOWN"

            if abs(transaction_total - holding_quantity) > Decimal("0.0001"):  # Allow for small rounding differences
                issues.append(f"Quantity mismatch for {stock_symbol}: holding shows {holding_quantity}, transactions calculate {transaction_total}")

        return issues

    def _check_portfolio_total_accuracy(self, portfolio_id: UUID) -> str:
        """Check if portfolio total_value matches sum of holdings."""
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return "Portfolio not found for total value check"

        # Use ORM query instead of raw SQL to see unflushed changes
        holdings = self.db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
        holdings_total = sum(holding.current_value or Decimal(0) for holding in holdings)

        if abs(portfolio.total_value - holdings_total) > Decimal("0.01"):  # Allow for small rounding
            return f"Portfolio total_value mismatch: portfolio shows {portfolio.total_value}, holdings sum to {holdings_total}"

        return ""

    def repair_portfolio_integrity(self, portfolio_id: UUID) -> List[str]:
        """
        Attempt to repair common portfolio integrity issues.
        Returns list of repairs performed.
        """
        repairs = []

        try:
            # Repair 1: Remove orphaned holdings
            orphaned_holdings_count = self.db.execute(text("""
                DELETE FROM holdings
                WHERE portfolio_id = :portfolio_id
                AND stock_id NOT IN (SELECT id FROM stocks)
            """), {"portfolio_id": str(portfolio_id)}).rowcount

            if orphaned_holdings_count > 0:
                repairs.append(f"Removed {orphaned_holdings_count} orphaned holdings")

            # Repair 2: Remove orphaned transactions (this is more dangerous, so we log it)
            orphaned_transactions = self.db.execute(text("""
                SELECT id FROM transactions
                WHERE portfolio_id = :portfolio_id
                AND stock_id NOT IN (SELECT id FROM stocks)
            """), {"portfolio_id": str(portfolio_id)}).fetchall()

            for (transaction_id,) in orphaned_transactions:
                self.log_warning(f"Found orphaned transaction {transaction_id} - manual review required")
                repairs.append(f"Found orphaned transaction {transaction_id} (not auto-deleted - manual review required)")

            # Repair 3: Remove zero-quantity holdings
            zero_holdings_count = self.db.execute(text("""
                DELETE FROM holdings
                WHERE portfolio_id = :portfolio_id AND quantity = 0
            """), {"portfolio_id": str(portfolio_id)}).rowcount

            if zero_holdings_count > 0:
                repairs.append(f"Removed {zero_holdings_count} zero-quantity holdings")

            # Repair 4: Recalculate portfolio totals
            self._recalculate_portfolio_totals(portfolio_id)
            repairs.append("Recalculated portfolio totals")

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self.log_error("Error during integrity repair", error=str(e))
            repairs.append(f"Repair failed: {str(e)}")

        return repairs

    def _recalculate_portfolio_totals(self, portfolio_id: UUID):
        """Recalculate and update portfolio totals from holdings."""
        totals = self.db.execute(text("""
            SELECT
                COALESCE(SUM(current_value), 0) as total_value,
                COALESCE(SUM(unrealized_gain_loss), 0) as total_unrealized,
                COALESCE(SUM(quantity * average_cost), 0) as total_cost_basis
            FROM holdings
            WHERE portfolio_id = :portfolio_id
        """), {"portfolio_id": str(portfolio_id)}).fetchone()

        total_value, total_unrealized, total_cost_basis = totals

        # Calculate daily change percentage
        daily_change_percent = Decimal(0)
        if total_cost_basis > 0:
            daily_change_percent = (total_unrealized / total_cost_basis) * 100

        # Update portfolio
        self.db.execute(text("""
            UPDATE portfolios
            SET
                total_value = :total_value,
                daily_change = :total_unrealized,
                daily_change_percent = :daily_change_percent
            WHERE id = :portfolio_id
        """), {
            "portfolio_id": str(portfolio_id),
            "total_value": float(total_value),
            "total_unrealized": float(total_unrealized),
            "daily_change_percent": float(daily_change_percent)
        })

    def ensure_data_consistency(self, portfolio_id: UUID) -> bool:
        """
        Ensure data consistency for a portfolio.
        Returns True if portfolio is consistent, False if issues remain.
        """
        issues = self.verify_portfolio_integrity(portfolio_id)

        if issues:
            self.log_warning(f"Portfolio integrity issues found: {issues}")
            repairs = self.repair_portfolio_integrity(portfolio_id)
            self.log_info(f"Repairs performed: {repairs}")

            # Re-check after repairs
            remaining_issues = self.verify_portfolio_integrity(portfolio_id)
            if remaining_issues:
                self.log_error(f"Portfolio integrity issues remain after repair: {remaining_issues}")
                return False

        return True
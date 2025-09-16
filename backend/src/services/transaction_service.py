"""
Transaction processing service with holdings management.
Provides atomic transaction processing that either succeeds completely or fails completely.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.core.exceptions import InsufficientSharesError, TransactionError
from src.core.logging import LoggerMixin
from src.models import Portfolio, Stock, Transaction, Holding
from src.models.transaction import TransactionType, SourceType
from src.schemas.transaction import TransactionCreate, TransactionResponse
from src.services.audit_service import AuditService


class TransactionService(LoggerMixin):
    """Service for atomic transaction processing with holdings updates."""
    
    def __init__(self, db: Session):
        self.db = db


def process_transaction(
    db: Session, 
    portfolio_id: UUID, 
    transaction_data: TransactionCreate
) -> TransactionResponse:
    """
    Process a transaction atomically - either everything succeeds or everything fails.
    
    For BUY transactions:
    - Create transaction record
    - Create new holding or update existing holding with new average cost
    
    For SELL transactions:
    - Verify sufficient shares are available
    - Create transaction record
    - Reduce holding quantity or remove holding if fully sold
    
    Args:
        db: Database session
        portfolio_id: UUID of the portfolio
        transaction_data: Transaction creation data
        
    Returns:
        TransactionResponse: The created transaction
        
    Raises:
        InsufficientSharesError: When trying to sell more shares than available
        TransactionError: When transaction processing fails
    """
    service = TransactionService(db)
    
    try:
        # Start transaction - everything in this function is atomic
        service.log_info("Processing transaction", 
                        portfolio_id=str(portfolio_id),
                        symbol=transaction_data.stock_symbol,
                        type=transaction_data.transaction_type.value,
                        quantity=str(transaction_data.quantity))
        
        # Verify portfolio exists
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.is_active.is_(True)
        ).first()
        
        if not portfolio:
            raise TransactionError(f"Portfolio not found: {portfolio_id}")
        
        # Find or create stock
        stock = db.query(Stock).filter(
            Stock.symbol == transaction_data.stock_symbol.upper()
        ).first()
        
        if not stock:
            stock = Stock(
                symbol=transaction_data.stock_symbol.upper(),
                company_name=f"{transaction_data.stock_symbol.upper()} Corporation",
                exchange="ASX"
            )
            db.add(stock)
            db.flush()  # Get ID without committing
        
        # Get existing holding if any
        holding = db.query(Holding).filter(
            Holding.portfolio_id == portfolio_id,
            Holding.stock_id == stock.id
        ).first()

        # Validate sell transactions
        if transaction_data.transaction_type == TransactionType.SELL:
            if not holding or holding.quantity < transaction_data.quantity:
                available_qty = holding.quantity if holding else Decimal("0")
                raise InsufficientSharesError(
                    symbol=transaction_data.stock_symbol.upper(),
                    requested=str(transaction_data.quantity),
                    available=str(available_qty)
                )
        
        # Calculate total amount including fees
        total_amount = (transaction_data.quantity * transaction_data.price_per_share) + (transaction_data.fees or Decimal("0"))
        
        # Create transaction record
        transaction = Transaction(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            transaction_type=transaction_data.transaction_type,
            quantity=transaction_data.quantity,
            price_per_share=transaction_data.price_per_share,
            total_amount=total_amount,
            fees=transaction_data.fees or Decimal("0"),
            transaction_date=transaction_data.transaction_date,
            source_type=SourceType.MANUAL,
            notes=transaction_data.notes,
            is_verified=True
        )
        
        db.add(transaction)
        db.flush()  # Get transaction ID
        
        # Update holdings based on transaction type
        if transaction_data.transaction_type == TransactionType.BUY:
            _process_buy_transaction(db, holding, stock, portfolio_id, transaction_data)
        elif transaction_data.transaction_type == TransactionType.SELL:
            _process_sell_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.DIVIDEND:
            _process_dividend_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.STOCK_SPLIT:
            _process_stock_split_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.BONUS_SHARES:
            _process_bonus_shares_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.TRANSFER_IN:
            _process_transfer_in_transaction(db, holding, stock, portfolio_id, transaction_data)
        elif transaction_data.transaction_type == TransactionType.TRANSFER_OUT:
            _process_transfer_out_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type in [TransactionType.REVERSE_SPLIT, TransactionType.SPIN_OFF, TransactionType.MERGER]:
            _process_corporate_action_transaction(db, holding, transaction_data)
        
        # Ensure all changes are flushed to the database before integrity check
        db.flush()

        # Update portfolio totals after processing transaction
        _update_portfolio_totals(db, portfolio_id)

        # Flush portfolio totals update as well
        db.flush()

        # Verify data integrity before committing
        from src.services.portfolio_integrity import PortfolioIntegrityService
        integrity_service = PortfolioIntegrityService(db)

        # Check for any integrity issues
        issues = integrity_service.verify_portfolio_integrity(portfolio_id)
        if issues:
            db.rollback()
            service.log_error("Portfolio integrity issues detected before commit", issues=issues)
            raise TransactionError(f"Transaction would cause data inconsistency: {'; '.join(issues)}")

        # Commit all changes atomically
        db.commit()

        # Final integrity check after commit
        if not integrity_service.ensure_data_consistency(portfolio_id):
            service.log_error("Portfolio integrity compromised after transaction")
            raise TransactionError("Transaction completed but data consistency cannot be guaranteed")

        # Reload transaction with stock relationship to ensure it's available for validation
        from sqlalchemy.orm import joinedload
        transaction_with_stock = db.query(Transaction).options(
            joinedload(Transaction.stock)
        ).filter(Transaction.id == transaction.id).first()

        # Create audit log for transaction creation
        # Note: We can't get user_id here since this service doesn't have access to request context
        # The audit logging will need to be added at the API layer where we have access to current_user

        service.log_info("Transaction processed successfully",
                        transaction_id=str(transaction.id),
                        portfolio_id=str(portfolio_id))

        return TransactionResponse.model_validate(transaction_with_stock)
        
    except InsufficientSharesError:
        # Validation errors - no rollback needed since no changes were made
        raise
    except TransactionError:
        # Business logic errors - rollback any partial changes
        db.rollback()
        raise
    except SQLAlchemyError as e:
        # Database errors - rollback and wrap in TransactionError
        db.rollback()
        service.log_error("Database error during transaction processing", error=str(e))
        raise TransactionError(f"Transaction processing failed: {str(e)}")
    except Exception as e:
        # Unexpected errors - rollback and wrap
        db.rollback()
        service.log_error("Unexpected error during transaction processing", error=str(e))
        raise TransactionError(f"Unexpected error during transaction processing: {str(e)}")


def _process_buy_transaction(
    db: Session,
    holding: Optional[Holding],
    stock: Stock,
    portfolio_id: UUID,
    transaction_data: TransactionCreate
) -> None:
    """Process a BUY transaction by creating or updating holdings."""

    if holding:
        # Update existing holding with new average cost including fees
        current_total_cost = holding.quantity * holding.average_cost
        transaction_cost = (transaction_data.quantity * transaction_data.price_per_share) + (transaction_data.fees or Decimal("0"))
        total_cost = current_total_cost + transaction_cost
        new_quantity = holding.quantity + transaction_data.quantity
        new_average_cost = total_cost / new_quantity

        holding.quantity = new_quantity
        holding.average_cost = new_average_cost
        # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!

    else:
        # Create new holding with fees included in average cost
        transaction_cost = (transaction_data.quantity * transaction_data.price_per_share) + (transaction_data.fees or Decimal("0"))
        average_cost_with_fees = transaction_cost / transaction_data.quantity

        holding = Holding(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            quantity=transaction_data.quantity,
            average_cost=average_cost_with_fees
            # No need for current_value, unrealized_gain_loss etc - they're calculated automatically!
        )
        db.add(holding)


def _process_sell_transaction(
    db: Session,
    holding: Holding,
    transaction_data: TransactionCreate
) -> None:
    """Process a SELL transaction by updating or removing holdings."""

    new_quantity = holding.quantity - transaction_data.quantity

    if new_quantity == 0:
        # Remove holding completely
        db.delete(holding)
    else:
        # Update holding quantity but keep same average cost
        holding.quantity = new_quantity
        # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!


def _process_dividend_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> None:
    """Process a DIVIDEND transaction - no holdings changes."""
    # Dividends don't affect holdings - they're just income records
    pass


def _process_stock_split_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> None:
    """Process a STOCK_SPLIT transaction by adding shares and adjusting average cost."""
    if not holding:
        raise TransactionError("Cannot process stock split for stock not held")

    # Add shares from split
    new_quantity = holding.quantity + transaction_data.quantity

    # Reduce average cost proportionally (same total cost basis, more shares)
    if new_quantity > 0:
        total_cost_basis = holding.quantity * holding.average_cost
        holding.average_cost = total_cost_basis / new_quantity

    holding.quantity = new_quantity
    # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!


def _process_bonus_shares_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> None:
    """Process a BONUS_SHARES transaction by adding shares and adjusting average cost."""
    if not holding:
        raise TransactionError("Cannot process bonus shares for stock not held")

    # Add bonus shares
    new_quantity = holding.quantity + transaction_data.quantity

    # Reduce average cost (same total cost basis, more shares)
    if new_quantity > 0:
        total_cost_basis = holding.quantity * holding.average_cost
        holding.average_cost = total_cost_basis / new_quantity

    holding.quantity = new_quantity
    # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!


def _process_transfer_in_transaction(
    db: Session,
    holding: Optional[Holding],
    stock: Stock,
    portfolio_id: UUID,
    transaction_data: TransactionCreate
) -> None:
    """Process a TRANSFER_IN transaction like a BUY transaction."""
    # Transfer in is essentially a buy transaction
    _process_buy_transaction(db, holding, stock, portfolio_id, transaction_data)


def _process_transfer_out_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> None:
    """Process a TRANSFER_OUT transaction like a SELL transaction."""
    # Transfer out is essentially a sell transaction
    _process_sell_transaction(db, holding, transaction_data)


def _process_corporate_action_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> None:
    """Process corporate actions (REVERSE_SPLIT, SPIN_OFF, MERGER)."""
    # For now, treat these as no-op transactions (just record keeping)
    # In a real system, these would have complex business logic
    pass


# New functions for edit/delete operations

def update_transaction(
    db: Session,
    portfolio_id: UUID,
    transaction_id: UUID,
    update_data: dict
) -> TransactionResponse:
    """
    Update a transaction atomically by recalculating all holdings from scratch.
    
    This ensures data consistency by:
    1. Updating the transaction
    2. Recalculating all holdings for affected stocks from all transactions
    """
    service = TransactionService(db)
    
    try:
        service.log_info("Updating transaction",
                        portfolio_id=str(portfolio_id),
                        transaction_id=str(transaction_id))
        
        # Get the transaction to update
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.portfolio_id == portfolio_id
        ).first()
        
        if not transaction:
            raise TransactionError(f"Transaction not found: {transaction_id}")
        
        # Store the stock ID for holdings recalculation
        stock_id = transaction.stock_id
        
        # Update transaction fields
        for field, value in update_data.items():
            if field == "stock_symbol":
                # Handle stock symbol change
                stock = db.query(Stock).filter(
                    Stock.symbol == value.upper()
                ).first()
                
                if not stock:
                    stock = Stock(
                        symbol=value.upper(),
                        company_name=f"{value.upper()} Corporation",
                        exchange="ASX"
                    )
                    db.add(stock)
                    db.flush()
                
                setattr(transaction, "stock_id", stock.id)
                # If stock changed, we need to recalculate holdings for both stocks
                old_stock_id = stock_id
                stock_id = stock.id
            else:
                setattr(transaction, field, value)
        
        # Recalculate total_amount if relevant fields changed
        if any(field in update_data for field in ["quantity", "price_per_share", "fees"]):
            fees = transaction.fees or Decimal("0")
            transaction.total_amount = (transaction.quantity * transaction.price_per_share) + fees
        
        # Recalculate holdings for the affected stock(s)
        _recalculate_holdings_for_stock(db, portfolio_id, stock_id)

        # If stock changed, also recalculate for the old stock
        if 'stock_symbol' in update_data and stock_id != transaction.stock_id:
            _recalculate_holdings_for_stock(db, portfolio_id, transaction.stock_id)

        # Update portfolio totals after updating transaction
        _update_portfolio_totals(db, portfolio_id)

        db.commit()
        db.refresh(transaction)
        
        service.log_info("Transaction updated successfully",
                        transaction_id=str(transaction_id))
        
        return TransactionResponse.model_validate(transaction)
        
    except Exception as e:
        db.rollback()
        service.log_error("Error updating transaction", error=str(e))
        raise TransactionError(f"Failed to update transaction: {str(e)}")


def delete_transaction(
    db: Session,
    portfolio_id: UUID,
    transaction_id: UUID
) -> None:
    """
    Delete a transaction atomically by recalculating holdings from remaining transactions.
    """
    service = TransactionService(db)
    
    try:
        service.log_info("Deleting transaction",
                        portfolio_id=str(portfolio_id),
                        transaction_id=str(transaction_id))
        
        # Get the transaction to delete
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.portfolio_id == portfolio_id
        ).first()
        
        if not transaction:
            raise TransactionError(f"Transaction not found: {transaction_id}")
        
        # Store the stock ID for holdings recalculation
        stock_id = transaction.stock_id
        
        # Delete the transaction
        db.delete(transaction)

        # Flush the deletion to ensure it's reflected in subsequent queries
        db.flush()

        # Recalculate holdings for the affected stock
        _recalculate_holdings_for_stock(db, portfolio_id, stock_id)

        # Update portfolio totals after deleting transaction
        _update_portfolio_totals(db, portfolio_id)

        db.commit()
        
        service.log_info("Transaction deleted successfully",
                        transaction_id=str(transaction_id))
        
    except Exception as e:
        db.rollback()
        service.log_error("Error deleting transaction", error=str(e))
        raise TransactionError(f"Failed to delete transaction: {str(e)}")


def _recalculate_holdings_for_stock(
    db: Session,
    portfolio_id: UUID,
    stock_id: UUID
) -> None:
    """
    Recalculate holdings for a specific stock by replaying all transactions.
    This ensures holdings are always consistent with the transaction history.
    """
    # Get all transactions for this stock in chronological order
    transactions = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.stock_id == stock_id
    ).order_by(Transaction.transaction_date.asc(), Transaction.processed_date.asc()).all()

    # Delete existing holding
    existing_holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.stock_id == stock_id
    ).first()
    if existing_holding:
        db.delete(existing_holding)

    # If no transactions remain, we're done (holding deleted)
    if not transactions:
        return
    
    # Replay all transactions to rebuild holdings
    holding = None
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    
    for transaction in transactions:
        transaction_data = TransactionCreate(
            stock_symbol=stock.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price_per_share=transaction.price_per_share,
            fees=transaction.fees,
            transaction_date=transaction.transaction_date,
            notes=transaction.notes
        )

        # Apply the transaction to holdings
        if transaction_data.transaction_type == TransactionType.BUY:
            holding = _replay_buy_transaction(db, holding, stock, portfolio_id, transaction_data)
        elif transaction_data.transaction_type == TransactionType.SELL:
            holding = _replay_sell_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.DIVIDEND:
            # Dividends don't affect holdings
            pass
        elif transaction_data.transaction_type == TransactionType.STOCK_SPLIT:
            holding = _replay_stock_split_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.BONUS_SHARES:
            holding = _replay_bonus_shares_transaction(db, holding, transaction_data)
        elif transaction_data.transaction_type == TransactionType.TRANSFER_IN:
            holding = _replay_buy_transaction(db, holding, stock, portfolio_id, transaction_data)
        elif transaction_data.transaction_type == TransactionType.TRANSFER_OUT:
            holding = _replay_sell_transaction(db, holding, transaction_data)


def _replay_buy_transaction(
    db: Session,
    holding: Optional[Holding],
    stock: Stock,
    portfolio_id: UUID,
    transaction_data: TransactionCreate
) -> Optional[Holding]:
    """Replay a buy transaction during holdings recalculation."""
    if holding:
        # Update existing holding with fees included in cost calculation
        current_total_cost = holding.quantity * holding.average_cost
        transaction_cost = (transaction_data.quantity * transaction_data.price_per_share) + (transaction_data.fees or Decimal("0"))
        total_cost = current_total_cost + transaction_cost
        new_quantity = holding.quantity + transaction_data.quantity
        new_average_cost = total_cost / new_quantity

        holding.quantity = new_quantity
        holding.average_cost = new_average_cost
        # No need to set current_value, unrealized_gain_loss etc - they're now hybrid properties!
    else:
        # Create new holding with fees included in average cost
        transaction_cost = (transaction_data.quantity * transaction_data.price_per_share) + (transaction_data.fees or Decimal("0"))
        average_cost_with_fees = transaction_cost / transaction_data.quantity
        holding = Holding(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            quantity=transaction_data.quantity,
            average_cost=average_cost_with_fees
            # No need for current_value, unrealized_gain_loss etc - they're calculated automatically!
        )
        db.add(holding)

    return holding


def _replay_sell_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> Optional[Holding]:
    """Replay a sell transaction during holdings recalculation."""
    if not holding:
        return None
    
    new_quantity = holding.quantity - transaction_data.quantity
    
    if new_quantity <= 0:
        # Remove holding completely
        db.delete(holding)
        return None
    else:
        # Update holding quantity but keep same average cost
        holding.quantity = new_quantity
        # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!
    
    return holding


def _replay_stock_split_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> Optional[Holding]:
    """Replay a stock split transaction during holdings recalculation."""
    if not holding:
        return None

    # Add shares from split
    new_quantity = holding.quantity + transaction_data.quantity

    # Reduce average cost proportionally (same total cost basis, more shares)
    if new_quantity > 0:
        total_cost_basis = holding.quantity * holding.average_cost
        holding.average_cost = total_cost_basis / new_quantity

    holding.quantity = new_quantity
    # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!

    return holding


def _replay_bonus_shares_transaction(
    db: Session,
    holding: Optional[Holding],
    transaction_data: TransactionCreate
) -> Optional[Holding]:
    """Replay a bonus shares transaction during holdings recalculation."""
    if not holding:
        return None

    # Add bonus shares
    new_quantity = holding.quantity + transaction_data.quantity

    # Reduce average cost (same total cost basis, more shares)
    if new_quantity > 0:
        total_cost_basis = holding.quantity * holding.average_cost
        holding.average_cost = total_cost_basis / new_quantity

    holding.quantity = new_quantity
    # No need to calculate current_value, unrealized_gain_loss etc - they're now hybrid properties!

    return holding

def _update_portfolio_totals(db: Session, portfolio_id: UUID) -> None:
    """Update portfolio total_value and daily_change based on current holdings."""
    
    # Get all current holdings for the portfolio
    holdings = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id
    ).all()

    # Calculate total current value from all holdings
    total_value = sum(holding.current_value for holding in holdings)

    # For daily change, we would need to compare with previous close prices
    # For now, calculate as total unrealized gain/loss
    total_unrealized_gain_loss = sum(holding.unrealized_gain_loss for holding in holdings)

    # Calculate daily change percentage  
    total_cost_basis = sum(holding.quantity * holding.average_cost for holding in holdings)
    daily_change_percent = Decimal("0.00")
    if total_cost_basis > 0:
        daily_change_percent = (total_unrealized_gain_loss / total_cost_basis) * 100

    # Update the portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio:
        portfolio.total_value = total_value
        portfolio.daily_change = total_unrealized_gain_loss  # Using unrealized gain as daily change for now
        portfolio.daily_change_percent = daily_change_percent

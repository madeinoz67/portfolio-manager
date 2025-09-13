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
        
        # Commit all changes atomically
        db.commit()
        db.refresh(transaction)
        
        service.log_info("Transaction processed successfully",
                        transaction_id=str(transaction.id),
                        portfolio_id=str(portfolio_id))
        
        return TransactionResponse.model_validate(transaction)
        
    except (InsufficientSharesError, TransactionError):
        # Re-raise business logic errors without wrapping
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
        # Update existing holding with new average cost
        total_cost = (holding.quantity * holding.average_cost) + (
            transaction_data.quantity * transaction_data.price_per_share
        )
        new_quantity = holding.quantity + transaction_data.quantity
        new_average_cost = total_cost / new_quantity
        
        holding.quantity = new_quantity
        holding.average_cost = new_average_cost
        # Use latest price as current price for now
        holding.current_value = new_quantity * transaction_data.price_per_share
        
        # Calculate unrealized gains
        cost_basis = new_quantity * new_average_cost
        holding.unrealized_gain_loss = holding.current_value - cost_basis
        if cost_basis > 0:
            holding.unrealized_gain_loss_percent = (holding.unrealized_gain_loss / cost_basis) * 100
        else:
            holding.unrealized_gain_loss_percent = Decimal("0.00")
            
    else:
        # Create new holding
        holding = Holding(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            quantity=transaction_data.quantity,
            average_cost=transaction_data.price_per_share,
            current_value=transaction_data.quantity * transaction_data.price_per_share,
            unrealized_gain_loss=Decimal("0.00"),
            unrealized_gain_loss_percent=Decimal("0.00")
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
        # Use latest price as current price for now
        holding.current_value = new_quantity * transaction_data.price_per_share
        
        # Calculate unrealized gains with new quantity
        cost_basis = new_quantity * holding.average_cost
        holding.unrealized_gain_loss = holding.current_value - cost_basis
        if cost_basis > 0:
            holding.unrealized_gain_loss_percent = (holding.unrealized_gain_loss / cost_basis) * 100
        else:
            holding.unrealized_gain_loss_percent = Decimal("0.00")
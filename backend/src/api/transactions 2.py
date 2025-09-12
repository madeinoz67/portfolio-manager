"""
Transaction API endpoints.
"""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio, Stock, Transaction
from src.models.transaction import SourceType
from src.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
)

router = APIRouter(prefix="/api/v1/portfolios", tags=["Transactions"])


@router.get("/{portfolio_id}/transactions", response_model=TransactionListResponse)
async def get_portfolio_transactions(
    portfolio_id: UUID,
    limit: Annotated[int, Query(description="Limit results", le=100)] = 50,
    offset: Annotated[int, Query(description="Offset for pagination", ge=0)] = 0,
    db: Annotated[Session, Depends(get_db)] = None
) -> TransactionListResponse:
    """Get portfolio transactions with pagination."""
    # Verify portfolio exists
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.is_active.is_(True)
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Get total count
    total = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id
    ).count()
    
    # Get transactions with pagination
    transactions = (
        db.query(Transaction)
        .filter(Transaction.portfolio_id == portfolio_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to response objects with stock data
    transaction_responses = []
    for transaction in transactions:
        # Load the stock relationship
        transaction_responses.append(TransactionResponse.model_validate(transaction))
    
    return TransactionListResponse(
        transactions=transaction_responses,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    portfolio_id: UUID,
    transaction_data: TransactionCreate,
    db: Annotated[Session, Depends(get_db)]
) -> TransactionResponse:
    """Create a new manual transaction."""
    # Verify portfolio exists
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.is_active.is_(True)
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Find or create stock
    stock = db.query(Stock).filter(
        Stock.symbol == transaction_data.stock_symbol.upper()
    ).first()
    
    if not stock:
        # For MVP, create a minimal stock record
        stock = Stock(
            symbol=transaction_data.stock_symbol.upper(),
            company_name=f"{transaction_data.stock_symbol.upper()} Corporation",
            exchange="ASX"
        )
        db.add(stock)
        db.flush()  # Get the ID without committing
    
    # Calculate total amount
    total_amount = transaction_data.quantity * transaction_data.price_per_share
    
    # Create transaction
    transaction = Transaction(
        portfolio_id=portfolio_id,
        stock_id=stock.id,
        transaction_type=transaction_data.transaction_type,
        quantity=transaction_data.quantity,
        price_per_share=transaction_data.price_per_share,
        total_amount=total_amount,
        fees=transaction_data.fees,
        transaction_date=transaction_data.transaction_date,
        source_type=SourceType.MANUAL,
        notes=transaction_data.notes,
        is_verified=True  # Manual transactions are pre-verified
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.model_validate(transaction)
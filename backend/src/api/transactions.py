"""
Transaction API endpoints.
"""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from src.database import get_db  
from src.models import Portfolio, Transaction
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
    
    # Get transactions with pagination and eager load stock relationship
    # Sort by transaction_date DESC, then by processed_date DESC for same-date transactions
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.stock))
        .filter(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.processed_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Convert to response objects with stock data (stock already loaded)
    transaction_responses = [
        TransactionResponse.model_validate(transaction) for transaction in transactions
    ]
    
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
    
    # Use the transaction service for atomic processing
    from src.services.transaction_service import process_transaction
    
    return process_transaction(db, portfolio_id, transaction_data)
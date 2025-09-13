"""
Transaction API endpoints.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from src.database import get_db  
from src.models import Portfolio, Transaction, Stock
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
    start_date: Annotated[Optional[date], Query(description="Filter transactions from this date (inclusive)")] = None,
    end_date: Annotated[Optional[date], Query(description="Filter transactions until this date (inclusive)")] = None,
    stock_symbol: Annotated[Optional[str], Query(description="Filter by stock symbol (case insensitive partial match)")] = None,
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
    
    # Build base query
    base_query = db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id)
    
    # Apply filters
    filters = []
    
    # Date range filtering
    if start_date:
        filters.append(Transaction.transaction_date >= start_date)
    if end_date:
        filters.append(Transaction.transaction_date <= end_date)
    
    # Stock symbol filtering (case insensitive partial match)
    if stock_symbol:
        # Join with Stock table for symbol filtering
        base_query = base_query.join(Stock, Transaction.stock_id == Stock.id)
        filters.append(func.upper(Stock.symbol).like(f"%{stock_symbol.upper()}%"))
    
    # Apply all filters
    if filters:
        base_query = base_query.filter(and_(*filters))
    
    # Get total count with filters applied
    total = base_query.count()
    
    # Get transactions with pagination and eager load stock relationship
    # Sort by transaction_date DESC, then by processed_date DESC for same-date transactions
    transactions = (
        base_query
        .options(joinedload(Transaction.stock))
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
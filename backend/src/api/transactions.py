"""
Transaction API endpoints.
"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from src.database import get_db
from src.core.dependencies import get_current_user_flexible
from src.models import Portfolio, Transaction, Stock, User
from src.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
)
from src.services.audit_service import AuditService

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
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> TransactionResponse:
    """Create a new manual transaction."""
    # Verify portfolio exists and belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Use the transaction service for atomic processing
    from src.services.transaction_service import process_transaction

    transaction_response = process_transaction(db, portfolio_id, transaction_data)

    # Create audit log for transaction creation
    try:
        audit_service = AuditService(db)
        # Get the actual transaction object from the database to access all fields
        transaction = db.query(Transaction).filter(Transaction.id == transaction_response.id).first()
        if transaction:
            audit_service.log_transaction_created(
                transaction=transaction,
                user_id=str(current_user.id),
                ip_address=getattr(request.client, 'host', None) if request.client else None,
                user_agent=request.headers.get('User-Agent')
            )
            db.commit()  # Commit audit log
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for transaction creation: {e}")

    return transaction_response


@router.get("/{portfolio_id}/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_detail(
    portfolio_id: UUID,
    transaction_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> TransactionResponse:
    """Get specific transaction details."""
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
    
    # Get transaction with stock relationship
    transaction = (
        db.query(Transaction)
        .options(joinedload(Transaction.stock))
        .filter(
            Transaction.id == transaction_id,
            Transaction.portfolio_id == portfolio_id
        )
        .first()
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return TransactionResponse.model_validate(transaction)


@router.put("/{portfolio_id}/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    portfolio_id: UUID,
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> TransactionResponse:
    """Update an existing transaction."""
    # Verify portfolio exists and belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Get transaction with stock relationship
    transaction = (
        db.query(Transaction)
        .options(joinedload(Transaction.stock))
        .filter(
            Transaction.id == transaction_id,
            Transaction.portfolio_id == portfolio_id
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Capture changes for audit log
    update_data = transaction_data.model_dump(exclude_unset=True)
    changes = {}
    for field, new_value in update_data.items():
        old_value = getattr(transaction, field, None)
        if old_value != new_value:
            changes[field] = {"old": old_value, "new": new_value}

    # Use the transaction service for atomic processing
    from src.services.transaction_service import update_transaction as update_transaction_service

    transaction_response = update_transaction_service(db, portfolio_id, transaction_id, update_data)

    # Create audit log for transaction update (only if there were actual changes)
    if changes:
        try:
            audit_service = AuditService(db)
            # Get the updated transaction object from the database
            updated_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
            if updated_transaction:
                audit_service.log_transaction_updated(
                    transaction=updated_transaction,
                    user_id=str(current_user.id),
                    changes=changes,
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )
                db.commit()  # Commit audit log
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for transaction update: {e}")

    return transaction_response


@router.delete("/{portfolio_id}/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    portfolio_id: UUID,
    transaction_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> None:
    """Delete a transaction."""
    # Verify portfolio exists and belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Get transaction with stock relationship for audit log
    transaction = (
        db.query(Transaction)
        .options(joinedload(Transaction.stock))
        .filter(
            Transaction.id == transaction_id,
            Transaction.portfolio_id == portfolio_id
        )
        .first()
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Store transaction details for audit log before deletion
    transaction_type = transaction.transaction_type.value
    symbol = transaction.stock.symbol if transaction.stock else "Unknown"

    # Create audit log before deletion (since transaction will be deleted)
    try:
        audit_service = AuditService(db)
        audit_service.log_transaction_deleted(
            transaction_id=str(transaction_id),
            transaction_type=transaction_type,
            symbol=symbol,
            user_id=str(current_user.id),
            portfolio_id=str(portfolio_id),
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        # Don't commit yet - we'll commit after the deletion
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for transaction deletion: {e}")

    # Use the transaction service for atomic processing
    from src.services.transaction_service import delete_transaction as delete_transaction_service

    delete_transaction_service(db, portfolio_id, transaction_id)

    # Commit the audit log after successful deletion
    try:
        db.commit()
    except Exception as e:
        # Log error but transaction has already been deleted
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to commit audit log for transaction deletion: {e}")
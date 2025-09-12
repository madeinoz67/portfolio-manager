"""
Performance API endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Portfolio
from src.schemas.performance import PerformanceMetrics, PerformancePeriod

router = APIRouter(prefix="/api/v1/portfolios", tags=["Performance"])


@router.get("/{portfolio_id}/performance", response_model=PerformanceMetrics)
async def get_portfolio_performance(
    portfolio_id: UUID,
    period: Annotated[PerformancePeriod, Query(description="Performance period")] = PerformancePeriod.ONE_MONTH,
    db: Annotated[Session, Depends(get_db)] = None
) -> PerformanceMetrics:
    """Get portfolio performance metrics for a specified period."""
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
    
    # For MVP, return mock performance data
    # In a real implementation, this would calculate actual performance metrics
    # based on transaction history, current market values, etc.
    
    mock_performance = PerformanceMetrics(
        total_return=Decimal("1250.50"),
        annualized_return=Decimal("8.75"),
        max_drawdown=Decimal("-5.20"),
        dividend_yield=Decimal("2.15"),
        period_start_value=Decimal("10000.00"),
        period_end_value=Decimal("11250.50"),
        total_dividends=Decimal("215.00"),
        period=period.value,
        calculated_at=datetime.utcnow()
    )
    
    return mock_performance
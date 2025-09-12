"""
Stock API endpoints.
"""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Stock, PriceHistory
from src.schemas.stock import StockResponse, StockDetailResponse, PricePointResponse

router = APIRouter(prefix="/api/v1/stocks", tags=["Stocks"])


@router.get("", response_model=list[StockResponse])
async def search_stocks(
    q: Annotated[Optional[str], Query(description="Search query (symbol or company name)")] = None,
    limit: Annotated[int, Query(description="Limit results", le=50)] = 20,
    db: Annotated[Session, Depends(get_db)] = None
) -> list[StockResponse]:
    """Search stocks by symbol or company name."""
    query = db.query(Stock)
    
    if q:
        search_term = f"%{q.upper()}%"
        query = query.filter(
            (Stock.symbol.like(search_term)) |
            (Stock.company_name.like(search_term))
        )
    
    stocks = query.limit(limit).all()
    return [StockResponse.model_validate(stock) for stock in stocks]


@router.get("/{stock_symbol}", response_model=StockDetailResponse)
async def get_stock(
    stock_symbol: str,
    db: Annotated[Session, Depends(get_db)]
) -> StockDetailResponse:
    """Get stock details by symbol."""
    stock = db.query(Stock).filter(
        Stock.symbol == stock_symbol.upper()
    ).first()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    return StockDetailResponse.model_validate(stock)


@router.get("/{stock_symbol}/price-history", response_model=list[PricePointResponse])
async def get_stock_price_history(
    stock_symbol: str,
    from_date: Annotated[Optional[date], Query(description="Start date")] = None,
    to_date: Annotated[Optional[date], Query(description="End date")] = None,
    period: Annotated[Optional[str], Query(description="Predefined period")] = None,
    db: Annotated[Session, Depends(get_db)] = None
) -> list[PricePointResponse]:
    """Get stock price history."""
    # First, verify the stock exists
    stock = db.query(Stock).filter(
        Stock.symbol == stock_symbol.upper()
    ).first()
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found"
        )
    
    # Validate period enum if provided
    if period:
        valid_periods = ["1W", "1M", "3M", "6M", "1Y", "2Y", "5Y"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
    
    # Get price history
    query = db.query(PriceHistory).filter(PriceHistory.stock_id == stock.id)
    
    # Apply date filters if provided
    if from_date:
        query = query.filter(PriceHistory.price_date >= from_date)
    if to_date:
        query = query.filter(PriceHistory.price_date <= to_date)
    
    # TODO: Handle period parameter with actual date calculations
    
    price_points = query.order_by(PriceHistory.price_date.desc()).all()
    
    return [
        PricePointResponse(
            date=p.price_date,
            open=p.open_price,
            high=p.high_price, 
            low=p.low_price,
            close=p.close_price,
            volume=p.volume
        )
        for p in price_points
    ]
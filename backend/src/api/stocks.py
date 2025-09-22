"""
Stock API endpoints.
"""

from datetime import date
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Stock
from src.models.stock import StockStatus
from src.schemas.stock import StockResponse, StockDetailResponse, PricePointResponse, StockCreateRequest
from src.services.adapter_market_data_service import AdapterMarketDataService
from pydantic import BaseModel

class StockValidationResponse(BaseModel):
    """Response for stock validation."""
    symbol: str
    is_valid: bool
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    error: Optional[str] = None

router = APIRouter(prefix="/api/v1/stocks", tags=["Stocks"])


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(
    stock_data: StockCreateRequest,
    db: Annotated[Session, Depends(get_db)]
) -> StockResponse:
    """Create a new stock."""
    # Check if stock already exists
    existing_stock = db.query(Stock).filter(Stock.symbol == stock_data.symbol.upper()).first()
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock with symbol {stock_data.symbol.upper()} already exists"
        )

    # Create new stock
    new_stock = Stock(
        symbol=stock_data.symbol.upper(),
        company_name=stock_data.company_name,
        exchange=stock_data.exchange.upper(),
        current_price=stock_data.current_price,
        status=stock_data.status
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return StockResponse.model_validate(new_stock)


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


@router.get("/search", response_model=List[StockResponse])
async def search_stocks_frontend(
    query: Annotated[str, Query(description="Search query (symbol or company name)")],
    limit: Annotated[int, Query(description="Limit results", le=50)] = 20,
    exchange: Annotated[Optional[str], Query(description="Filter by exchange")] = None,
    sector: Annotated[Optional[str], Query(description="Filter by sector")] = None,
    db: Annotated[Session, Depends(get_db)] = None
) -> List[StockResponse]:
    """Search stocks for frontend - matches existing stocks or tries to find new ones."""

    # First search existing stocks in database
    query_obj = db.query(Stock)

    search_term = f"%{query.upper()}%"
    query_obj = query_obj.filter(
        (Stock.symbol.like(search_term)) |
        (Stock.company_name.like(search_term))
    )

    if exchange:
        query_obj = query_obj.filter(Stock.exchange == exchange.upper())

    existing_stocks = query_obj.limit(limit).all()

    # If we have results, return them
    if existing_stocks:
        return [StockResponse.model_validate(stock) for stock in existing_stocks]

    # No results found in database, try to validate as a stock symbol via yfinance
    if len(query) <= 5 and query.isalpha():  # Likely a stock symbol
        service = AdapterMarketDataService(db)
        try:
            price_data = await service.fetch_price(query.upper())

            if price_data and price_data.get("company_name"):
                # Valid stock, create it
                new_stock = Stock(
                    symbol=query.upper(),
                    company_name=price_data["company_name"],
                    exchange=price_data.get("exchange", "UNKNOWN"),
                    status=StockStatus.ACTIVE,
                    current_price=price_data.get("price"),
                    last_price_update=price_data.get("source_timestamp")
                )

                db.add(new_stock)
                db.commit()
                db.refresh(new_stock)

                return [StockResponse.model_validate(new_stock)]

        except Exception as e:
            print(f"Error fetching stock data for {query}: {e}")
        finally:
            await service.close_session()

    # No results found
    return []


@router.get("/suggestions", response_model=List[StockResponse])
async def get_stock_suggestions(
    query: Annotated[str, Query(description="Search query for suggestions")],
    limit: Annotated[int, Query(description="Limit results", le=20)] = 10,
    db: Annotated[Session, Depends(get_db)] = None
) -> List[StockResponse]:
    """Get stock suggestions for autocomplete."""

    if len(query) < 1:
        return []

    search_term = f"%{query.upper()}%"
    stocks = db.query(Stock).filter(
        (Stock.symbol.like(search_term)) |
        (Stock.company_name.like(search_term))
    ).limit(limit).all()

    return [StockResponse.model_validate(stock) for stock in stocks]


@router.get("/validate/{symbol}", response_model=StockValidationResponse)
async def validate_stock_symbol(
    symbol: str,
    db: Annotated[Session, Depends(get_db)]
) -> StockValidationResponse:
    """
    Validate a stock symbol using live market data.

    This endpoint validates the stock symbol by:
    1. Checking if it exists in the local database
    2. If not found, using the adapter system to fetch live data from market providers
    3. Returning validation status with current price and company details
    """
    symbol = symbol.upper().strip()

    if not symbol:
        return StockValidationResponse(
            symbol=symbol,
            is_valid=False,
            error="Symbol cannot be empty"
        )

    # First check if stock already exists in database
    existing_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if existing_stock:
        return StockValidationResponse(
            symbol=symbol,
            is_valid=True,
            company_name=existing_stock.company_name,
            current_price=float(existing_stock.current_price) if existing_stock.current_price else None,
            exchange=existing_stock.exchange,
            currency="AUD" if existing_stock.exchange == "ASX" else "USD"
        )

    # Stock doesn't exist locally, validate via adapter system
    service = AdapterMarketDataService(db)
    try:
        price_data = await service.fetch_price(symbol)

        if price_data and price_data.get("price") is not None:
            # Stock is valid, return live data from adapter
            return StockValidationResponse(
                symbol=symbol,
                is_valid=True,
                company_name=price_data.get("company_name"),
                current_price=price_data.get("price"),
                exchange=price_data.get("exchange"),
                currency=price_data.get("currency")
            )
        else:
            # Invalid stock symbol
            return StockValidationResponse(
                symbol=symbol,
                is_valid=False,
                error=f"Stock symbol '{symbol}' not found or invalid"
            )

    except Exception as e:
        # Error during validation
        return StockValidationResponse(
            symbol=symbol,
            is_valid=False,
            error=f"Error validating stock: {str(e)}"
        )

    finally:
        await service.close_session()


@router.get("/search/{symbol}", response_model=StockResponse)
async def search_or_create_stock(
    symbol: str,
    db: Annotated[Session, Depends(get_db)]
) -> StockResponse:
    """Search for a stock by symbol, create if not found and valid via yfinance."""
    symbol = symbol.upper()

    # First check if stock already exists in database
    existing_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if existing_stock:
        return StockResponse.model_validate(existing_stock)

    # Stock doesn't exist, try to fetch from yfinance to validate and get company info
    service = AdapterMarketDataService(db)
    try:
        price_data = await service.fetch_price(symbol)

        if price_data and price_data.get("company_name"):
            # Stock is valid, create it
            new_stock = Stock(
                symbol=symbol,
                company_name=price_data["company_name"],
                exchange=price_data.get("exchange", "UNKNOWN"),
                status=StockStatus.ACTIVE,
                current_price=price_data.get("price"),
                last_price_update=price_data.get("source_timestamp")
            )

            db.add(new_stock)
            db.commit()
            db.refresh(new_stock)

            return StockResponse.model_validate(new_stock)

    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")

    finally:
        await service.close_session()

    # Stock not found or invalid
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Stock {symbol} not found and could not be validated"
    )


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


# Price history endpoint removed - legacy price_history table no longer exists.
# Future implementation should use realtime_price_history data for charting.
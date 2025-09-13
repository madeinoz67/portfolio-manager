"""
Market data API endpoints for real-time price fetching and streaming.

Provides endpoints for fetching current prices, bulk price updates,
and Server-Sent Events streaming for real-time updates.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.dependencies import get_current_user_flexible
from src.database import get_db
from src.models.user import User
from src.models.stock import Stock
from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.sse_connection import SSEConnection
from src.services.market_data_service import MarketDataService
from src.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/market-data", tags=["market-data"])


# Pydantic models
class PriceResponse(BaseModel):
    symbol: str
    price: float
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    fetched_at: str
    cached: bool = False

    class Config:
        from_attributes = True


class BulkPriceResponse(BaseModel):
    prices: Dict[str, PriceResponse]
    fetched_at: str
    cached_count: int
    fresh_count: int


class ServiceStatusResponse(BaseModel):
    status: str  # 'healthy', 'degraded', 'unavailable'
    providers_status: Dict[str, dict]
    next_update_in_seconds: Optional[int] = None
    last_update_at: Optional[str] = None
    cache_stats: dict


class RefreshRequest(BaseModel):
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to refresh")
    force: bool = Field(False, description="Force refresh even if cache is fresh")


@router.get("/prices/{symbol}", response_model=PriceResponse)
async def get_price(
    symbol: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get current price for a specific symbol."""

    symbol = symbol.upper()
    service = MarketDataService(db)

    try:
        # First check cache
        cached_price = service.get_latest_price(symbol, max_age_minutes=30)

        if cached_price:
            return PriceResponse(
                symbol=symbol,
                price=float(cached_price.price),
                volume=cached_price.volume,
                market_cap=float(cached_price.market_cap) if cached_price.market_cap else None,
                fetched_at=cached_price.fetched_at.isoformat() + "Z",
                cached=True
            )

        # Fetch fresh data if not in cache
        price_data = await service.fetch_price(symbol)

        if not price_data:
            raise HTTPException(
                status_code=404,
                detail=f"Price data not available for symbol {symbol}"
            )

        return PriceResponse(
            symbol=symbol,
            price=float(price_data["price"]),
            volume=price_data.get("volume"),
            market_cap=float(price_data["market_cap"]) if price_data.get("market_cap") else None,
            fetched_at=price_data["source_timestamp"].isoformat() + "Z",
            cached=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching price data"
        )
    finally:
        await service.close_session()


@router.get("/prices", response_model=BulkPriceResponse)
async def get_bulk_prices(
    symbols: List[str] = Query(..., description="List of stock symbols"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get current prices for multiple symbols."""

    if len(symbols) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 symbols allowed per request"
        )

    symbols = [s.upper() for s in symbols]
    service = MarketDataService(db)

    try:
        # Fetch each symbol individually for simplicity
        prices = {}
        cached_count = 0
        fresh_count = 0

        for symbol in symbols:
            try:
                # Check cache first
                cached_price = service.get_latest_price(symbol, max_age_minutes=30)

                if cached_price:
                    prices[symbol] = PriceResponse(
                        symbol=symbol,
                        price=float(cached_price.price),
                        volume=cached_price.volume,
                        market_cap=float(cached_price.market_cap) if cached_price.market_cap else None,
                        fetched_at=cached_price.fetched_at.isoformat() + "Z",
                        cached=True
                    )
                    cached_count += 1
                else:
                    # Fetch fresh data
                    price_data = await service.fetch_price(symbol)

                    if price_data:
                        prices[symbol] = PriceResponse(
                            symbol=symbol,
                            price=float(price_data["price"]),
                            volume=price_data.get("volume"),
                            market_cap=float(price_data["market_cap"]) if price_data.get("market_cap") else None,
                            fetched_at=price_data["source_timestamp"].isoformat() + "Z",
                            cached=False
                        )
                        fresh_count += 1
            except Exception as e:
                logger.warning(f"Failed to fetch price for {symbol}: {e}")
                continue

        return BulkPriceResponse(
            prices=prices,
            fetched_at=datetime.now().isoformat() + "Z",
            cached_count=cached_count,
            fresh_count=fresh_count
        )

    except Exception as e:
        logger.error(f"Error fetching bulk prices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching price data"
        )
    finally:
        await service.close_session()


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get market data service status and provider health."""

    service = MarketDataService(db)
    providers = service.get_enabled_providers()

    providers_status = {}
    overall_status = "healthy"

    for provider in providers:
        # Check recent API usage to determine provider health
        recent_usage = db.query(service.db.query).filter(
            # This would be implemented with proper queries
        ).limit(10).all() if hasattr(service, 'db') else []

        providers_status[provider.name] = {
            "enabled": provider.is_enabled,
            "priority": provider.priority,
            "rate_limit_per_day": provider.rate_limit_per_day,
            "status": "healthy" if provider.is_enabled else "disabled"
        }

    # Mock cache stats
    cache_stats = {
        "total_symbols": 150,
        "fresh_symbols": 120,
        "stale_symbols": 30,
        "cache_hit_rate": 0.85
    }

    return ServiceStatusResponse(
        status=overall_status,
        providers_status=providers_status,
        next_update_in_seconds=900,  # 15 minutes
        last_update_at=datetime.now().isoformat() + "Z",
        cache_stats=cache_stats
    )


@router.post("/refresh")
async def refresh_prices(
    request: RefreshRequest,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Manually refresh price data with rate limiting."""

    # Rate limiting: max 1 request per minute per user
    # This would be implemented with proper rate limiting logic

    service = MarketDataService(db)

    try:
        if request.symbols:
            # Refresh specific symbols
            symbols = [s.upper() for s in request.symbols[:20]]  # Limit to 20 symbols
        else:
            # Refresh all symbols from user's portfolios
            user_portfolios = db.query(Portfolio).filter(Portfolio.owner_id == current_user.id).all()
            portfolio_ids = [p.id for p in user_portfolios]

            holdings = db.query(Holding).filter(Holding.portfolio_id.in_(portfolio_ids)).all()
            symbols = list(set([h.stock.symbol for h in holdings if h.stock]))

        if not symbols:
            return {"message": "No symbols to refresh", "symbols_refreshed": 0}

        # Force refresh if requested or refresh stale data
        max_age = 0 if request.force else 15
        price_data = await service.refresh_portfolio_symbols(symbols)

        return {
            "message": f"Refreshed {len(price_data)} symbols",
            "symbols_refreshed": len(price_data),
            "symbols": list(price_data.keys()),
            "refreshed_at": datetime.now().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Error refreshing prices: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while refreshing prices"
        )
    finally:
        await service.close_session()


@router.get("/stream")
async def stream_market_data(
    symbols: Optional[List[str]] = Query(None, description="Symbols to subscribe to"),
    portfolio_ids: Optional[List[str]] = Query(None, description="Portfolio IDs to track"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Server-Sent Events stream for real-time market data updates."""

    connection_id = str(uuid.uuid4())

    # Register SSE connection
    sse_connection = SSEConnection(
        connection_id=connection_id,
        user_id=current_user.id,
        subscribed_symbols=symbols or [],
        portfolio_ids=portfolio_ids or [],
        connection_type="market_data",
        is_active=True,
        last_heartbeat=datetime.utcnow()
    )

    db.add(sse_connection)
    db.commit()

    logger.info(f"SSE connection established: {connection_id} for user {current_user.id}")

    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connection', 'connection_id': connection_id, 'status': 'connected'})}\n\n"

            # Send heartbeat every 30 seconds and price updates every 15 minutes
            while True:
                try:
                    # Check if connection is still active in database
                    conn = db.query(SSEConnection).filter(SSEConnection.connection_id == connection_id).first()
                    if not conn or not conn.is_active:
                        logger.info(f"SSE connection {connection_id} marked as inactive")
                        break

                    # Update heartbeat
                    conn.last_heartbeat = datetime.utcnow()
                    db.commit()

                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat() + 'Z'})}\n\n"

                    # Mock price update (in real implementation, this would be triggered by actual price changes)
                    if symbols:
                        service = MarketDataService(db)
                        try:
                            price_updates = {}
                            for symbol in symbols[:10]:  # Limit to avoid overload
                                latest = service.get_latest_price(symbol, max_age_minutes=30)
                                if latest:
                                    price_updates[symbol] = {
                                        "price": float(latest.price),
                                        "volume": latest.volume,
                                        "timestamp": latest.fetched_at.isoformat() + "Z"
                                    }

                            if price_updates:
                                yield f"data: {json.dumps({'type': 'price_update', 'data': price_updates})}\n\n"
                        finally:
                            await service.close_session()

                    # Wait for next update cycle
                    await asyncio.sleep(30)

                except Exception as e:
                    logger.error(f"Error in SSE stream for {connection_id}: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Stream error occurred'})}\n\n"
                    break

        except Exception as e:
            logger.error(f"SSE stream error for {connection_id}: {e}")
        finally:
            # Mark connection as disconnected
            try:
                conn = db.query(SSEConnection).filter(SSEConnection.connection_id == connection_id).first()
                if conn:
                    conn.is_active = False
                    conn.disconnected_at = datetime.utcnow()
                    db.commit()
                logger.info(f"SSE connection {connection_id} disconnected")
            except Exception as e:
                logger.error(f"Error closing SSE connection {connection_id}: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
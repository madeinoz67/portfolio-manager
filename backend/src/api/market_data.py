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

from src.core.dependencies import get_current_user_flexible, get_current_admin_user
from src.database import get_db
from src.models.user import User
from src.models.stock import Stock
from src.models.portfolio import Portfolio
from src.models.holding import Holding
from src.models.sse_connection import SSEConnection
from src.models.api_usage_metrics import ApiUsageMetrics
from src.models.market_data_provider import ProviderActivity
from src.services.market_data_service import MarketDataService
from src.services.activity_service import log_provider_activity
from src.core.logging import get_logger
from sqlalchemy import func, and_, or_

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


class SchedulerStatusResponse(BaseModel):
    scheduler: dict
    recent_activity: dict
    provider_stats: dict


class SchedulerControlRequest(BaseModel):
    action: str  # 'pause' or 'restart'


class SchedulerControlResponse(BaseModel):
    success: bool
    message: str
    new_status: str


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
        # For now, skip the recent usage check as it's not fully implemented
        recent_usage = []

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


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get scheduler status and metrics (admin only)."""

    try:
        # Get scheduler status from the background task (would need global state tracking in real implementation)
        from src.main import background_task, scheduler_paused

        # Improved scheduler running detection - check both task state and recent activity
        task_running = background_task is not None and not background_task.done() and not scheduler_paused

        # Also check if we have recent activity (within last 20 minutes) as backup detection
        twenty_minutes_ago = datetime.utcnow() - timedelta(minutes=20)
        recent_scheduler_activity = db.query(ProviderActivity).filter(
            and_(
                ProviderActivity.activity_type.in_(["API_CALL", "BULK_PRICE_UPDATE", "HEALTH_CHECK"]),
                ProviderActivity.timestamp >= twenty_minutes_ago
            )
        ).first()

        # Consider scheduler running if either task is active OR we have recent activity
        scheduler_running = task_running or (recent_scheduler_activity is not None and not scheduler_paused)

        # Calculate scheduler stats from activities
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        last_24_hours = datetime.utcnow() - timedelta(hours=24)

        # Get recent activities for stats - filter only API_CALL and BULK_PRICE_UPDATE for scheduler runs
        recent_activities = db.query(ProviderActivity).filter(
            ProviderActivity.timestamp >= last_24_hours
        ).all()

        # Filter for scheduler-related activities only
        scheduler_activities = [a for a in recent_activities if a.activity_type in ["API_CALL", "BULK_PRICE_UPDATE", "BATCH_SUMMARY"]]

        successful_runs = len([a for a in scheduler_activities if a.status == "success"])
        failed_runs = len([a for a in scheduler_activities if a.status == "error"])
        total_runs = len(scheduler_activities)

        # Get latest scheduler activity for last run time
        latest_activity = db.query(ProviderActivity).filter(
            ProviderActivity.activity_type.in_(["API_CALL", "BULK_PRICE_UPDATE", "BATCH_SUMMARY"])
        ).order_by(ProviderActivity.timestamp.desc()).first()

        # Calculate success rate
        success_rate = successful_runs / total_runs if total_runs > 0 else 0.0

        # Calculate average response time from metadata (only API_CALL activities have response times)
        api_call_activities = [a for a in recent_activities if a.activity_type == "API_CALL"]
        response_times = []
        for activity in api_call_activities:
            if activity.activity_metadata and 'response_time_ms' in activity.activity_metadata:
                try:
                    response_times.append(int(activity.activity_metadata['response_time_ms']))
                except (ValueError, TypeError):
                    continue

        # Return average response time as integer ms (or None if no data)
        avg_response_time_ms = int(sum(response_times) / len(response_times)) if response_times else None

        # Calculate restart metrics for monitoring
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Count restart events in different time periods - include all types of restarts
        restart_activities = db.query(ProviderActivity).filter(
            and_(
                ProviderActivity.provider_id == "system",
                ProviderActivity.activity_type == "SCHEDULER_CONTROL",
                or_(
                    ProviderActivity.description.like("%restarted%"),
                    ProviderActivity.description.like("%restart%"),
                    ProviderActivity.description.like("%started%")
                ),
                ProviderActivity.timestamp >= last_24_hours
            )
        ).all()

        restarts_last_hour = len([a for a in restart_activities if a.timestamp >= one_hour_ago])
        restarts_last_24_hours = len(restart_activities)

        # Calculate restart trend (comparing last hour to average hourly rate over 24h)
        avg_hourly_restart_rate = restarts_last_24_hours / 24.0
        restart_trend = "increasing" if restarts_last_hour > (avg_hourly_restart_rate * 1.5) else "stable"

        # Get API usage metrics
        api_metrics = db.query(ApiUsageMetrics).filter(
            ApiUsageMetrics.recorded_at >= one_hour_ago
        ).all()

        # Build provider stats
        provider_stats = {}
        service = MarketDataService(db)
        providers = service.get_enabled_providers()

        for provider in providers:
            provider_activities = [a for a in recent_activities if a.provider_id == provider.name]
            provider_api_calls = [m for m in api_metrics if m.provider_id == provider.name]

            calls_last_hour = len(provider_api_calls)
            successful_calls = len([a for a in provider_activities if a.status == "success"])
            total_calls = len(provider_activities)
            provider_success_rate = successful_calls / total_calls if total_calls > 0 else 0.0

            # Get last successful call
            last_successful = None
            for activity in sorted(provider_activities, key=lambda x: x.timestamp, reverse=True):
                if activity.status == "success":
                    last_successful = activity.timestamp.isoformat() + "Z"
                    break

            provider_stats[provider.name] = {
                "calls_last_hour": calls_last_hour,
                "success_rate": provider_success_rate,
                "avg_response_time_ms": avg_response_time_ms,
                "last_successful_call": last_successful
            }

        # Calculate total symbols processed from scheduler activities only
        symbols_processed = len(set([
            a.activity_metadata.get('symbol')
            for a in api_call_activities
            if a.activity_metadata and 'symbol' in a.activity_metadata
        ]))

        # Mock uptime calculation (would be real in production)
        uptime_seconds = 3600 if scheduler_running else 0  # Mock 1 hour uptime

        # Check for recurring errors that might indicate scheduler problems
        scheduler_error_message = None

        # Look for database constraint errors in recent activities
        recent_times = [a.timestamp for a in scheduler_activities[-10:]]  # Last 10 activities
        if len(recent_times) >= 3:
            # Check if activities are clustered (indicating restarts)
            time_diffs = [(recent_times[i] - recent_times[i-1]).total_seconds() for i in range(1, len(recent_times))]
            avg_interval = sum(time_diffs) / len(time_diffs) if time_diffs else 0

            # If average interval is much shorter than expected 15-minute cycles (900 seconds)
            # This indicates the scheduler is restarting frequently
            if avg_interval < 300 and total_runs > 5:  # Less than 5 minutes between runs
                scheduler_error_message = "Scheduler appears to be restarting frequently - check logs for database errors"

        # Determine status based on task state and pause flag
        if scheduler_paused:
            scheduler_status = "paused"
        elif scheduler_running:
            if scheduler_error_message:
                scheduler_status = "error"
            else:
                scheduler_status = "running"
        else:
            scheduler_status = "stopped"

        # Calculate next run time more intelligently
        next_run_at = None
        if not scheduler_paused:
            if scheduler_running and not scheduler_error_message:
                # Calculate based on last activity + 15 minutes, or now + 15 minutes, whichever is later
                from src.utils.datetime_utils import now
                current_local_time = now()
                if latest_activity:
                    next_from_last = latest_activity.timestamp + timedelta(minutes=15)
                    next_from_now = current_local_time + timedelta(minutes=2)  # Give a small buffer
                    next_run_at = max(next_from_last, next_from_now).isoformat()
                else:
                    next_run_at = (current_local_time + timedelta(minutes=2)).isoformat()

        return SchedulerStatusResponse(
            scheduler={
                "status": scheduler_status,
                "uptime_seconds": uptime_seconds,
                "next_run_at": next_run_at,
                "last_run_at": latest_activity.timestamp.isoformat() + "Z" if latest_activity else None,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "error_message": scheduler_error_message,
                "restarts_last_hour": restarts_last_hour,
                "restarts_last_24_hours": restarts_last_24_hours,
                "restart_trend": restart_trend
            },
            recent_activity={
                "total_symbols_processed": symbols_processed,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time_ms
            },
            provider_stats=provider_stats
        )

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching scheduler status"
        )


@router.post("/scheduler/control", response_model=SchedulerControlResponse)
async def control_scheduler(
    request: SchedulerControlRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Control scheduler (pause/restart) - admin only."""

    try:
        from src.main import background_task, restart_background_task, pause_background_task

        if request.action == "pause":
            success = await pause_background_task()
            if success:
                # Log the pause action
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="SCHEDULER_CONTROL",
                    description="Scheduler paused by admin",
                    status="warning",
                    metadata={"admin_user": current_admin.email, "action": "pause"}
                )
                return SchedulerControlResponse(
                    success=True,
                    message="Scheduler paused successfully",
                    new_status="paused"
                )
            else:
                return SchedulerControlResponse(
                    success=False,
                    message="Failed to pause scheduler or scheduler already paused",
                    new_status="unknown"
                )

        elif request.action == "restart":
            success = await restart_background_task()
            if success:
                # Log the restart action
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="SCHEDULER_CONTROL",
                    description="Scheduler restarted by admin",
                    status="success",
                    metadata={"admin_user": current_admin.email, "action": "restart"}
                )
                return SchedulerControlResponse(
                    success=True,
                    message="Scheduler restarted successfully",
                    new_status="running"
                )
            else:
                return SchedulerControlResponse(
                    success=False,
                    message="Failed to restart scheduler",
                    new_status="unknown"
                )
        else:
            return SchedulerControlResponse(
                success=False,
                message=f"Invalid action '{request.action}'. Use 'pause' or 'restart'",
                new_status="unknown"
            )

    except Exception as e:
        logger.error(f"Error controlling scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while controlling scheduler"
        )
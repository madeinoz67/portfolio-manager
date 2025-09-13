"""
Admin API endpoints for market data management.

Provides administrative controls for market data polling and usage monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, Integer, cast
from pydantic import BaseModel, Field, validator

from src.core.dependencies import get_current_user_flexible
from src.database import get_db
from src.models.user import User
from src.models.poll_interval_config import PollIntervalConfig
from src.models.api_usage_metrics import ApiUsageMetrics

router = APIRouter(prefix="/api/v1/admin", tags=["admin-market-data"])


# Pydantic models for request/response
class PollIntervalCreate(BaseModel):
    interval_minutes: int = Field(..., ge=1, le=1440, description="Polling interval in minutes (1-1440)")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for the interval change")


class PollIntervalResponse(BaseModel):
    id: str
    interval_minutes: int
    reason: str
    created_at: str
    created_by: str
    is_active: bool
    expired_at: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('created_at', 'expired_at', pre=True)
    def format_datetime(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat() + "Z"
        return value

    @validator('id', pre=True)
    def format_uuid(cls, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        return value


class ApiUsageSummary(BaseModel):
    total_requests_today: int
    total_requests_this_month: int
    errors_today: int
    success_rate_today: float


class ApiUsageByProvider(BaseModel):
    provider_name: str
    requests_today: int
    requests_this_month: int
    errors_today: int
    rate_limit_remaining: int
    rate_limit_total: int
    last_request_at: Optional[str] = None


class ApiUsageByDate(BaseModel):
    date: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    unique_symbols: int


class RateLimits(BaseModel):
    daily_limit: int
    hourly_limit: int
    minute_limit: int
    current_usage: dict


class ApiUsageResponse(BaseModel):
    summary: ApiUsageSummary
    by_provider: List[ApiUsageByProvider]
    by_date: List[ApiUsageByDate]
    rate_limits: RateLimits
    last_updated: str


@router.get("/api-usage", response_model=ApiUsageResponse)
async def get_api_usage(
    start_date: Optional[str] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    provider: Optional[str] = Query(None, description="Filter by provider (alpha_vantage, yfinance)"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get API usage metrics and statistics."""

    # Build base query
    base_query = db.query(ApiUsageMetrics)

    # Apply filters
    if provider:
        base_query = base_query.filter(ApiUsageMetrics.provider_name == provider)

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            base_query = base_query.filter(ApiUsageMetrics.created_date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            base_query = base_query.filter(ApiUsageMetrics.created_date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    # Calculate summary metrics
    today = datetime.now().date()
    month_start = today.replace(day=1)

    today_metrics = db.query(ApiUsageMetrics).filter(
        func.date(ApiUsageMetrics.created_date) == today
    ).all()

    month_metrics = db.query(ApiUsageMetrics).filter(
        ApiUsageMetrics.created_date >= month_start
    ).all()

    total_today = len(today_metrics)
    errors_today = len([m for m in today_metrics if not m.success])
    success_rate = (total_today - errors_today) / total_today * 100 if total_today > 0 else 100.0

    summary = ApiUsageSummary(
        total_requests_today=total_today,
        total_requests_this_month=len(month_metrics),
        errors_today=errors_today,
        success_rate_today=round(success_rate, 2)
    )

    # Get provider statistics
    provider_stats = {}
    for provider_name in ["alpha_vantage", "yfinance"]:
        provider_today = [m for m in today_metrics if m.provider_name == provider_name]
        provider_month = [m for m in month_metrics if m.provider_name == provider_name]

        last_request = db.query(ApiUsageMetrics).filter(
            ApiUsageMetrics.provider_name == provider_name
        ).order_by(desc(ApiUsageMetrics.request_timestamp)).first()

        # Mock rate limits (in real implementation, these would come from provider configs)
        rate_limits = {
            "alpha_vantage": {"remaining": 500, "total": 500},
            "yfinance": {"remaining": 2000, "total": 2000}
        }

        provider_stats[provider_name] = ApiUsageByProvider(
            provider_name=provider_name,
            requests_today=len(provider_today),
            requests_this_month=len(provider_month),
            errors_today=len([m for m in provider_today if not m.success]),
            rate_limit_remaining=rate_limits[provider_name]["remaining"],
            rate_limit_total=rate_limits[provider_name]["total"],
            last_request_at=last_request.request_timestamp.isoformat() + "Z" if last_request else None
        )

    by_provider = [stats for stats in provider_stats.values() if provider is None or stats.provider_name == provider]

    # Get daily statistics
    daily_stats = db.query(
        func.date(ApiUsageMetrics.created_date).label('date'),
        func.count().label('total'),
        func.sum(cast(ApiUsageMetrics.success, Integer)).label('successful'),
        func.count(func.distinct(ApiUsageMetrics.symbol)).label('unique_symbols')
    ).group_by(func.date(ApiUsageMetrics.created_date)).order_by(desc('date'))

    if start_date:
        daily_stats = daily_stats.filter(func.date(ApiUsageMetrics.created_date) >= start_date)
    if end_date:
        daily_stats = daily_stats.filter(func.date(ApiUsageMetrics.created_date) <= end_date)

    if limit:
        daily_stats = daily_stats.limit(limit)
    if offset:
        daily_stats = daily_stats.offset(offset)

    by_date = []
    for row in daily_stats.all():
        by_date.append(ApiUsageByDate(
            date=row.date.isoformat(),
            total_requests=row.total,
            successful_requests=row.successful or 0,
            failed_requests=row.total - (row.successful or 0),
            unique_symbols=row.unique_symbols or 0
        ))

    # Mock rate limits
    rate_limits = RateLimits(
        daily_limit=2000,
        hourly_limit=100,
        minute_limit=10,
        current_usage={
            "daily": total_today,
            "hourly": len([m for m in today_metrics if m.request_timestamp >= datetime.now() - timedelta(hours=1)]),
            "minute": len([m for m in today_metrics if m.request_timestamp >= datetime.now() - timedelta(minutes=1)])
        }
    )

    return ApiUsageResponse(
        summary=summary,
        by_provider=by_provider,
        by_date=by_date,
        rate_limits=rate_limits,
        last_updated=datetime.now().isoformat() + "Z"
    )


@router.get("/poll-intervals", response_model=List[PollIntervalResponse])
async def get_poll_intervals(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get poll interval configurations."""

    query = db.query(PollIntervalConfig).order_by(desc(PollIntervalConfig.created_at))

    if active is not None:
        query = query.filter(PollIntervalConfig.is_active == active)

    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    configs = query.all()

    return [
        PollIntervalResponse(
            id=str(config.id),
            interval_minutes=config.interval_minutes,
            reason=config.reason,
            created_at=config.created_at.isoformat() + "Z",
            created_by=config.created_by,
            is_active=config.is_active,
            expired_at=config.expired_at.isoformat() + "Z" if config.expired_at else None
        )
        for config in configs
    ]


@router.post("/poll-intervals", response_model=PollIntervalResponse, status_code=status.HTTP_201_CREATED)
async def create_poll_interval(
    poll_interval: PollIntervalCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Create a new poll interval configuration."""

    # Deactivate existing active configurations
    db.query(PollIntervalConfig).filter(
        PollIntervalConfig.is_active == True
    ).update({
        "is_active": False,
        "expired_at": datetime.utcnow()
    })

    # Create new configuration
    new_config = PollIntervalConfig(
        interval_minutes=poll_interval.interval_minutes,
        reason=poll_interval.reason,
        created_by=current_user.email,
        is_active=True
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    response = PollIntervalResponse(
        id=str(new_config.id),
        interval_minutes=new_config.interval_minutes,
        reason=new_config.reason,
        created_at=new_config.created_at.isoformat() + "Z",
        created_by=new_config.created_by,
        is_active=new_config.is_active,
        expired_at=None
    )

    return response
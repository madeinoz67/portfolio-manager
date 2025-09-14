"""
Admin API endpoints for user management and system administration.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel

from src.core.dependencies import get_current_admin_user, get_db
from src.core.logging import get_logger
from src.models.user import User
from src.models.user_role import UserRole
from src.models.portfolio import Portfolio
from src.models.api_usage_metrics import ApiUsageMetrics
from src.models.market_data_provider import ProviderActivity
from src.schemas.auth import UserResponse
from src.utils.datetime_utils import to_iso_string, utc_now

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class SystemMetrics(BaseModel):
    totalUsers: int
    totalPortfolios: int
    activeUsers: int
    adminUsers: int
    systemStatus: str
    lastUpdated: str


class AdminUserListItem(BaseModel):
    id: str
    email: str
    firstName: str | None = None
    lastName: str | None = None
    role: str
    isActive: bool
    createdAt: str
    portfolioCount: int
    lastLoginAt: str | None = None


class PaginatedUsersResponse(BaseModel):
    users: List[AdminUserListItem]
    total: int
    page: int
    pages: int


@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    role: str = Query(None, description="Filter by role"),
    active: bool = Query(None, description="Filter by active status")
) -> PaginatedUsersResponse:
    """
    List all users in the system with pagination.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting user list")

    # Build query with filters
    query = db.query(User)

    if role:
        if role == "admin":
            query = query.filter(User.role == UserRole.ADMIN)
        elif role == "user":
            query = query.filter(User.role == UserRole.USER)

    if active is not None:
        query = query.filter(User.is_active == active)

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * size
    pages = (total + size - 1) // size  # Ceiling division

    # Get paginated results
    users = query.offset(offset).limit(size).all()

    # Build response with portfolio counts
    user_list = []
    for user in users:
        portfolio_count = db.query(Portfolio).filter(Portfolio.owner_id == user.id).count()

        user_list.append(AdminUserListItem(
            id=str(user.id),
            email=user.email,
            firstName=user.first_name,
            lastName=user.last_name,
            role=user.role.value,
            isActive=user.is_active,
            createdAt=to_iso_string(user.created_at),
            portfolioCount=portfolio_count,
            lastLoginAt=None  # TODO: Track login times in future
        ))

    return PaginatedUsersResponse(
        users=user_list,
        total=total,
        page=page,
        pages=pages
    )


class AdminPortfolioSummary(BaseModel):
    id: str
    name: str
    value: float
    lastUpdated: str


class AdminUserDetails(BaseModel):
    id: str
    email: str
    firstName: str | None = None
    lastName: str | None = None
    role: str
    isActive: bool
    createdAt: str
    portfolioCount: int
    lastLoginAt: str | None = None
    totalAssets: float
    portfolios: List[AdminPortfolioSummary]


@router.get("/users/{user_id}", response_model=AdminUserDetails)
async def get_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> AdminUserDetails:
    """
    Get enhanced details of a specific user including portfolio information.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting details for user {user_id}")

    from fastapi import HTTPException, status

    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid user ID format"
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's portfolios with values
    portfolios = db.query(Portfolio).filter(Portfolio.owner_id == user.id).all()

    portfolio_summaries = []
    total_assets = 0.0

    for portfolio in portfolios:
        # Use portfolio.total_value or calculate from holdings
        portfolio_value = float(portfolio.total_value or 0.0)
        total_assets += portfolio_value

        portfolio_summaries.append(AdminPortfolioSummary(
            id=str(portfolio.id),
            name=portfolio.name,
            value=portfolio_value,
            lastUpdated=to_iso_string(portfolio.updated_at)
        ))

    return AdminUserDetails(
        id=str(user.id),
        email=user.email,
        firstName=user.first_name,
        lastName=user.last_name,
        role=user.role.value,
        isActive=user.is_active,
        createdAt=to_iso_string(user.created_at),
        portfolioCount=len(portfolios),
        lastLoginAt=None,  # TODO: Track login times in future
        totalAssets=total_assets,
        portfolios=portfolio_summaries
    )


@router.get("/system/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> SystemMetrics:
    """
    Get system-wide metrics and statistics.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting system metrics")

    # Calculate metrics from database
    total_users = db.query(User).count()
    total_portfolios = db.query(Portfolio).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()

    # Determine system status
    system_status = "healthy"
    if admin_users == 0:
        system_status = "error"
    elif total_users == 0:
        system_status = "warning"

    return SystemMetrics(
        totalUsers=total_users,
        totalPortfolios=total_portfolios,
        activeUsers=active_users,
        adminUsers=admin_users,
        systemStatus=system_status,
        lastUpdated=to_iso_string(utc_now())
    )


# Market Data Models for compatibility
class MarketDataStatus(BaseModel):
    providerId: str
    providerName: str
    isEnabled: bool
    lastUpdate: str
    apiCallsToday: int
    monthlyLimit: int
    monthlyUsage: int
    costPerCall: float
    status: str
    supportsBulkFetch: bool = False
    bulkFetchLimit: Optional[int] = None


class MarketDataStatusResponse(BaseModel):
    providers: List[MarketDataStatus]


@router.get("/market-data/status", response_model=MarketDataStatusResponse)
async def get_market_data_status(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get market data providers status from real database."""
    logger.info(f"Admin user {current_admin.email} requesting market data provider status")

    from src.models.market_data_provider import MarketDataProvider
    from src.models.api_usage_metrics import ApiUsageMetrics
    from sqlalchemy import func
    from datetime import datetime, date

    today = date.today()
    current_month_start = datetime(today.year, today.month, 1)

    # Get all providers from database
    providers = db.query(MarketDataProvider).all()

    # Get today's usage stats per provider
    today_usage = db.query(
        ApiUsageMetrics.provider_id,
        func.sum(ApiUsageMetrics.requests_count).label('calls_today'),
        func.avg(ApiUsageMetrics.avg_response_time_ms).label('avg_response_time')
    ).filter(
        func.date(ApiUsageMetrics.recorded_at) == today
    ).group_by(ApiUsageMetrics.provider_id).all()

    # Get monthly usage stats per provider
    monthly_usage = db.query(
        ApiUsageMetrics.provider_id,
        func.sum(ApiUsageMetrics.requests_count).label('calls_this_month'),
        func.sum(ApiUsageMetrics.cost_estimate).label('total_cost')
    ).filter(
        ApiUsageMetrics.recorded_at >= current_month_start
    ).group_by(ApiUsageMetrics.provider_id).all()

    # Create lookup dictionaries
    today_lookup = {stat.provider_id: {
        'calls': int(stat.calls_today or 0),
        'avg_response_time': int(stat.avg_response_time or 0)
    } for stat in today_usage}
    monthly_lookup = {stat.provider_id: {
        'calls': int(stat.calls_this_month or 0),
        'cost': float(stat.total_cost or 0.0)
    } for stat in monthly_usage}

    # Check for rate limit hits today
    rate_limit_hits = db.query(ApiUsageMetrics.provider_id).filter(
        func.date(ApiUsageMetrics.recorded_at) == today,
        ApiUsageMetrics.rate_limit_hit == True
    ).group_by(ApiUsageMetrics.provider_id).all()

    rate_limited_providers = {hit.provider_id for hit in rate_limit_hits}

    provider_list = []
    for provider in providers:
        today_data = today_lookup.get(provider.name, {'calls': 0, 'avg_response_time': 0})
        calls_today = today_data['calls']
        avg_response_time = today_data['avg_response_time']
        monthly_data = monthly_lookup.get(provider.name, {'calls': 0, 'cost': 0.0})

        # Determine status based on provider state and recent usage
        if not provider.is_enabled:
            status = "inactive"
        elif provider.name in rate_limited_providers:
            status = "rate_limited"
        elif calls_today > 0:
            status = "active"
        else:
            status = "idle"

        # Calculate cost per call (avoid division by zero)
        calls_this_month = monthly_data['calls']
        total_cost = monthly_data['cost']
        cost_per_call = (total_cost / calls_this_month) if calls_this_month > 0 else 0.0

        # Determine bulk fetch support based on provider type
        supports_bulk = False
        bulk_limit = None

        if provider.name == "yfinance":
            supports_bulk = True
            bulk_limit = None  # yfinance doesn't have a specific limit documented
        elif provider.name == "alpha_vantage":
            supports_bulk = True
            bulk_limit = 100  # Alpha Vantage REALTIME_BULK_QUOTES supports up to 100 symbols

        provider_list.append({
            "providerId": provider.name,
            "providerName": provider.display_name,
            "isEnabled": provider.is_enabled,
            "lastUpdate": to_iso_string(provider.updated_at),
            "apiCallsToday": calls_today,
            "monthlyLimit": provider.rate_limit_per_day * 30,  # Approximate monthly limit
            "monthlyUsage": calls_this_month,
            "costPerCall": round(cost_per_call, 4),
            "status": status,
            "avgResponseTimeMs": avg_response_time,
            "supportsBulkFetch": supports_bulk,
            "bulkFetchLimit": bulk_limit
        })

    return {
        "providers": provider_list
    }


# API Usage Models
class ApiUsageSummary(BaseModel):
    total_requests_today: int
    total_requests_this_month: int
    success_rate_today: float
    total_errors_today: int


class ApiUsageByProvider(BaseModel):
    provider_name: str
    requests_today: int
    errors_today: int
    requests_this_month: int
    success_rate: float


class ApiUsageResponse(BaseModel):
    summary: ApiUsageSummary
    by_provider: List[ApiUsageByProvider]


@router.get("/api-usage", response_model=ApiUsageResponse)
async def get_api_usage(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get API usage statistics and metrics from real database."""
    logger.info(f"Admin user {current_admin.email} requesting API usage statistics")

    # Use provider_activities table for consistency with provider detail page
    from src.models.market_data_provider import ProviderActivity
    from sqlalchemy import func, and_
    from datetime import datetime, date, timedelta

    today = utc_now().date()
    current_month_start = datetime(today.year, today.month, 1)

    # Get today's activities
    today_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) == today
    ).all()

    # Get this month's activities
    month_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) >= current_month_start.date()
    ).all()

    # Calculate summary statistics from provider activities
    total_requests_today = len(today_activities)
    total_errors_today = len([a for a in today_activities if a.status == "error"])
    total_requests_this_month = len(month_activities)

    # Calculate success rate
    if total_requests_today > 0:
        success_rate_today = ((total_requests_today - total_errors_today) / total_requests_today) * 100
    else:
        success_rate_today = 0.0

    # Get by provider statistics from activities
    provider_stats_dict = {}
    for activity in today_activities:
        provider_id = activity.provider_id
        if provider_id not in provider_stats_dict:
            provider_stats_dict[provider_id] = {"requests": 0, "errors": 0}

        provider_stats_dict[provider_id]["requests"] += 1
        if activity.status == "error":
            provider_stats_dict[provider_id]["errors"] += 1

    # Convert to the expected format
    provider_stats = []
    for provider_id, stats in provider_stats_dict.items():
        class ProviderStat:
            def __init__(self, provider_id, requests, errors):
                self.provider_id = provider_id
                self.requests_today = requests
                self.errors_today = errors

        provider_stats.append(ProviderStat(provider_id, stats["requests"], stats["errors"]))

    # Get monthly stats by provider from activities
    monthly_provider_stats_dict = {}
    for activity in month_activities:
        provider_id = activity.provider_id
        if provider_id not in monthly_provider_stats_dict:
            monthly_provider_stats_dict[provider_id] = 0
        monthly_provider_stats_dict[provider_id] += 1

    # Create monthly lookup dict
    monthly_lookup = monthly_provider_stats_dict

    # Build provider response
    by_provider = []
    for provider_stat in provider_stats:
        requests_today = int(provider_stat.requests_today or 0)
        errors_today = int(provider_stat.errors_today or 0)
        requests_this_month = int(monthly_lookup.get(provider_stat.provider_id, 0))

        # Calculate provider success rate
        if requests_today > 0:
            success_rate = ((requests_today - errors_today) / requests_today) * 100
        else:
            success_rate = 0.0

        by_provider.append({
            "provider_name": provider_stat.provider_id,
            "requests_today": requests_today,
            "errors_today": errors_today,
            "requests_this_month": requests_this_month,
            "success_rate": round(success_rate, 1)
        })

    # Calculate trends compared to yesterday
    yesterday = today - timedelta(days=1)
    daily_change_percent = 0.0

    yesterday_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) == yesterday
    ).all()

    total_requests_yesterday = len(yesterday_activities)

    if total_requests_yesterday > 0:
        daily_change_percent = ((total_requests_today - total_requests_yesterday) / total_requests_yesterday) * 100

    # Calculate weekly change (7 days ago)
    week_ago = today - timedelta(days=7)
    weekly_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) == week_ago
    ).all()

    total_requests_week_ago = len(weekly_activities)
    weekly_change_count = total_requests_today - total_requests_week_ago

    return {
        "summary": {
            "total_requests_today": total_requests_today,
            "total_requests_this_month": total_requests_this_month,
            "success_rate_today": round(success_rate_today, 1),
            "total_errors_today": total_errors_today
        },
        "by_provider": by_provider,
        "trends": {
            "daily_change_percent": round(daily_change_percent, 1),
            "weekly_change_count": weekly_change_count
        }
    }


# Provider Toggle Models
class ProviderToggleResponse(BaseModel):
    providerId: str
    providerName: str
    isEnabled: bool
    message: str


# Provider Detail Models
class UsageStatsToday(BaseModel):
    totalRequests: int
    totalErrors: int
    totalCost: float
    avgResponseTime: int
    rateLimitHits: int
    successRate: float

class UsageStatsHistorical(BaseModel):
    last7Days: dict
    last30Days: dict

class UsageStats(BaseModel):
    today: UsageStatsToday
    yesterday: UsageStatsToday
    historical: UsageStatsHistorical

class PerformanceMetrics(BaseModel):
    successRate: float
    errorRate: float
    avgResponseTime: int
    uptimePercentage: float

class ProviderConfiguration(BaseModel):
    apiEndpoint: str
    authentication: str
    rateLimits: dict
    timeout: int

class RecentActivity(BaseModel):
    timestamp: str
    type: str
    description: str
    status: str

class CostBreakdownItem(BaseModel):
    requestType: str
    count: int
    cost: float

class CostAnalysis(BaseModel):
    totalCostToday: float
    totalCostThisMonth: float
    projectedMonthlyCost: float
    costPerRequest: float
    costBreakdown: List[CostBreakdownItem]

class ProviderDetailResponse(BaseModel):
    providerId: str
    providerName: str
    isEnabled: bool
    priority: int
    rateLimitPerMinute: int
    rateLimitPerDay: int
    lastUpdated: str
    usageStats: UsageStats
    performanceMetrics: PerformanceMetrics
    configuration: ProviderConfiguration
    recentActivity: List[RecentActivity]
    costAnalysis: CostAnalysis


class ActivityItem(BaseModel):
    providerId: str
    providerName: str
    type: str
    description: str
    status: str
    timestamp: str


class ActivitiesResponse(BaseModel):
    activities: List[ActivityItem]
    pagination: Optional[dict] = None


@router.patch("/market-data/providers/{provider_id}/toggle", response_model=ProviderToggleResponse)
async def toggle_market_data_provider(
    provider_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle market data provider enabled/disabled status."""
    logger.info(f"Admin user {current_admin.email} toggling provider {provider_id}")

    from src.models.market_data_provider import MarketDataProvider
    from src.utils.datetime_utils import now
    from fastapi import HTTPException

    # Find the provider
    provider = db.query(MarketDataProvider).filter(MarketDataProvider.name == provider_id).first()

    if not provider:
        logger.warning(f"Provider {provider_id} not found")
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Provider '{provider_id}' not found"}
        )

    # Toggle the enabled status
    original_status = provider.is_enabled
    provider.is_enabled = not provider.is_enabled
    provider.updated_at = now()

    try:
        db.commit()
        db.refresh(provider)

        action = "enabled" if provider.is_enabled else "disabled"
        message = f"Provider '{provider.display_name}' has been {action}"

        logger.info(f"Provider {provider_id} {action} successfully")

        return ProviderToggleResponse(
            providerId=provider.name,
            providerName=provider.display_name,
            isEnabled=provider.is_enabled,
            message=message
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to toggle provider {provider_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "Failed to update provider status"}
        )


@router.get("/market-data/providers/{provider_id}/details", response_model=ProviderDetailResponse)
async def get_provider_details(
    provider_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive details and statistics for a specific provider."""
    logger.info(f"Admin user {current_admin.email} requesting details for provider {provider_id}")

    from src.models.market_data_provider import MarketDataProvider
    from fastapi import HTTPException

    # Find the provider
    provider = db.query(MarketDataProvider).filter(MarketDataProvider.name == provider_id).first()

    if not provider:
        logger.warning(f"Provider {provider_id} not found")
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Provider '{provider_id}' not found"}
        )

    # Get real usage statistics from provider activities
    from src.services.activity_service import get_recent_activities
    from src.models.market_data_provider import ProviderActivity
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_

    # Calculate date ranges
    today = utc_now().date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    # Get today's stats
    today_activities = db.query(ProviderActivity).filter(
        and_(
            ProviderActivity.provider_id == provider_id,
            func.date(ProviderActivity.timestamp) == today
        )
    ).all()

    today_total_requests = len(today_activities)
    today_errors = len([a for a in today_activities if a.status == "error"])
    today_success_rate = ((today_total_requests - today_errors) / max(today_total_requests, 1)) * 100

    # Calculate average response time from metadata where available
    today_response_times = []
    for activity in today_activities:
        if activity.activity_metadata and 'response_time_ms' in activity.activity_metadata:
            today_response_times.append(activity.activity_metadata['response_time_ms'])
        elif activity.activity_metadata and 'response_time' in activity.activity_metadata:
            today_response_times.append(activity.activity_metadata['response_time'])

    avg_response_time_today = int(sum(today_response_times) / len(today_response_times)) if today_response_times else 0

    today_stats = UsageStatsToday(
        totalRequests=today_total_requests,
        totalErrors=today_errors,
        totalCost=0.0,  # No cost tracking yet
        avgResponseTime=avg_response_time_today,
        rateLimitHits=len([a for a in today_activities if "RATE_LIMIT" in a.activity_type]),
        successRate=round(today_success_rate, 1)
    )

    # Get yesterday's stats
    yesterday_activities = db.query(ProviderActivity).filter(
        and_(
            ProviderActivity.provider_id == provider_id,
            func.date(ProviderActivity.timestamp) == yesterday
        )
    ).all()

    yesterday_total_requests = len(yesterday_activities)
    yesterday_errors = len([a for a in yesterday_activities if a.status == "error"])
    yesterday_success_rate = ((yesterday_total_requests - yesterday_errors) / max(yesterday_total_requests, 1)) * 100

    yesterday_response_times = []
    for activity in yesterday_activities:
        if activity.activity_metadata and 'response_time_ms' in activity.activity_metadata:
            yesterday_response_times.append(activity.activity_metadata['response_time_ms'])
        elif activity.activity_metadata and 'response_time' in activity.activity_metadata:
            yesterday_response_times.append(activity.activity_metadata['response_time'])

    avg_response_time_yesterday = int(sum(yesterday_response_times) / len(yesterday_response_times)) if yesterday_response_times else 0

    yesterday_stats = UsageStatsToday(
        totalRequests=yesterday_total_requests,
        totalErrors=yesterday_errors,
        totalCost=0.0,
        avgResponseTime=avg_response_time_yesterday,
        rateLimitHits=len([a for a in yesterday_activities if "RATE_LIMIT" in a.activity_type]),
        successRate=round(yesterday_success_rate, 1)
    )

    # Get historical data for last 7 and 30 days
    last7days_dict = {}
    last30days_dict = {}

    # Group activities by date for the last 7 days
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        day_activities = db.query(ProviderActivity).filter(
            and_(
                ProviderActivity.provider_id == provider_id,
                func.date(ProviderActivity.timestamp) == date
            )
        ).all()

        requests = len(day_activities)
        errors = len([a for a in day_activities if a.status == "error"])

        last7days_dict[date_str] = {"requests": requests, "errors": errors}

    # Group activities by date for the last 30 days
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        day_activities = db.query(ProviderActivity).filter(
            and_(
                ProviderActivity.provider_id == provider_id,
                func.date(ProviderActivity.timestamp) == date
            )
        ).all()

        requests = len(day_activities)
        errors = len([a for a in day_activities if a.status == "error"])

        last30days_dict[date_str] = {"requests": requests, "errors": errors}

    # Provider configuration
    config = {
        "apiEndpoint": provider.base_url or f"https://api.{provider.name}.com",
        "authentication": "API Key" if provider.api_key else "None",
        "rateLimits": {
            "perMinute": provider.rate_limit_per_minute,
            "perDay": provider.rate_limit_per_day
        },
        "timeout": 30
    }

    # Get real recent activity from the database
    recent_activities = get_recent_activities(
        db_session=db,
        provider_id=provider_id,
        limit=10
    )

    recent_activity = []
    for activity in recent_activities:
        # Extract metadata for additional fields
        metadata = activity.activity_metadata or {}

        activity_item = {
            "timestamp": to_iso_string(activity.timestamp),
            "type": activity.activity_type,
            "description": activity.description,
            "status": activity.status
        }

        # Add optional fields from metadata
        if "symbols" in metadata:
            activity_item["requestCount"] = len(metadata["symbols"]) if isinstance(metadata["symbols"], list) else 1
        elif "successful_fetches" in metadata:
            activity_item["requestCount"] = metadata["successful_fetches"]
        else:
            activity_item["requestCount"] = 1

        if "response_time_ms" in metadata:
            activity_item["responseTime"] = metadata["response_time_ms"]
        elif "response_time" in metadata:
            activity_item["responseTime"] = metadata["response_time"]

        if "error_count" in metadata:
            activity_item["errorCount"] = metadata["error_count"]
        elif activity.status == "error":
            activity_item["errorCount"] = 1
        else:
            activity_item["errorCount"] = 0

        # Map activity types to request types for UI
        if "BULK" in activity.activity_type:
            activity_item["requestType"] = "bulk_price_fetch"
        elif "API_CALL" in activity.activity_type:
            activity_item["requestType"] = "price_fetch"
        elif "HEALTH_CHECK" in activity.activity_type:
            activity_item["requestType"] = "health_check"
        else:
            activity_item["requestType"] = "unknown"

        recent_activity.append(activity_item)

    # Calculate real cost breakdown based on today's activities
    cost_breakdown = []
    request_types = {}

    for activity in today_activities:
        request_type = "unknown"
        if "BULK" in activity.activity_type:
            request_type = "bulk_price_fetch"
        elif "API_CALL" in activity.activity_type:
            request_type = "price_fetch"
        elif "HEALTH_CHECK" in activity.activity_type:
            request_type = "health_check"

        if request_type not in request_types:
            request_types[request_type] = 0
        request_types[request_type] += 1

    for request_type, count in request_types.items():
        cost_breakdown.append({
            "requestType": request_type,
            "count": count,
            "cost": 0.0  # No cost tracking implemented yet
        })

    # If no activities today, add default entry
    if not cost_breakdown:
        cost_breakdown.append({
            "requestType": "price_fetch",
            "count": 0,
            "cost": 0.0
        })

    return ProviderDetailResponse(
        providerId=provider.name,
        providerName=provider.display_name,
        isEnabled=provider.is_enabled,
        priority=provider.priority,
        rateLimitPerMinute=provider.rate_limit_per_minute,
        rateLimitPerDay=provider.rate_limit_per_day,
        lastUpdated=to_iso_string(provider.updated_at),
        usageStats=UsageStats(
            today=today_stats,
            yesterday=yesterday_stats,
            historical=UsageStatsHistorical(
                last7Days=last7days_dict,
                last30Days=last30days_dict
            )
        ),
        performanceMetrics=PerformanceMetrics(
            successRate=round(today_success_rate, 1),
            errorRate=round(100 - today_success_rate, 1),
            avgResponseTime=avg_response_time_today,
            uptimePercentage=99.5 if provider.is_enabled else 0.0
        ),
        configuration=ProviderConfiguration(
            apiEndpoint=config["apiEndpoint"],
            authentication=config["authentication"],
            rateLimits=config["rateLimits"],
            timeout=config["timeout"]
        ),
        recentActivity=recent_activity,
        costAnalysis=CostAnalysis(
            totalCostToday=0.0,
            totalCostThisMonth=0.0,
            projectedMonthlyCost=0.0,
            costPerRequest=0.0,
            costBreakdown=cost_breakdown
        )
    )

@router.get("/market-data/activities", response_model=ActivitiesResponse)
async def get_market_data_activities(
    provider: Optional[List[str]] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get market data provider activities with filtering and pagination."""
    from src.models.market_data_provider import MarketDataProvider, ProviderActivity
    from src.services.activity_service import get_recent_activities_all_providers
    import math

    logger.info(f"Admin user {current_admin.email} requesting activities")

    # Get activities with filters
    activities = get_recent_activities_all_providers(
        db_session=db,
        provider_filter=provider,
        status_filter=status,
        page=page,
        size=size
    )

    # Get provider names for display
    providers = {p.name: p.display_name for p in db.query(MarketDataProvider).all()}

    # Convert to response format
    activity_items = []
    for activity in activities:
        activity_items.append(ActivityItem(
            providerId=activity.provider_id,
            providerName=providers.get(activity.provider_id, activity.provider_id),
            type=activity.activity_type,
            description=activity.description,
            status=activity.status,
            timestamp=to_iso_string(activity.timestamp)
        ))

    # Calculate pagination info
    total_query = db.query(ProviderActivity)
    if provider:
        if isinstance(provider, list):
            total_query = total_query.filter(ProviderActivity.provider_id.in_(provider))
        else:
            total_query = total_query.filter(ProviderActivity.provider_id == provider)
    if status:
        total_query = total_query.filter(ProviderActivity.status == status)

    total = total_query.count()
    pages = math.ceil(total / size) if total > 0 else 1

    pagination = {
        "page": page,
        "size": size,
        "total": total,
        "pages": pages
    }

    return ActivitiesResponse(
        activities=activity_items,
        pagination=pagination
    )


class DashboardActivity(BaseModel):
    id: str
    provider_id: str
    provider_name: str
    activity_type: str
    description: str
    status: str  # success, warning, error, info
    timestamp: str
    relative_time: str  # "2 minutes ago", "1 hour ago"
    metadata: Optional[dict] = None


class DashboardActivitiesResponse(BaseModel):
    activities: List[DashboardActivity]
    summary: dict


def calculate_relative_time(timestamp: datetime) -> str:
    """Calculate relative time string from timestamp."""
    from src.utils.datetime_utils import utc_now

    # Get current UTC time for comparison
    now = utc_now()

    # Ensure both timestamps are naive UTC for comparison
    if timestamp.tzinfo is not None:
        # Convert timezone-aware timestamp to naive UTC
        timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    # Ensure now is also naive UTC (our utc_now should already be naive)
    if hasattr(now, 'tzinfo') and now.tzinfo is not None:
        now = now.replace(tzinfo=None)

    # Calculate the difference
    diff = now - timestamp

    # Handle future timestamps (should not happen, but just in case)
    if diff.total_seconds() < 0:
        return "just now"

    total_seconds = diff.total_seconds()

    if total_seconds < 10:  # Less than 10 seconds
        return "just now"
    elif total_seconds < 60:  # Less than 1 minute
        seconds = int(total_seconds)
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:  # Days
        days = int(total_seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


@router.get("/dashboard/recent-activities", response_model=DashboardActivitiesResponse)
async def get_dashboard_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    reset: bool = Query(False, description="Reset activities with correct timestamps"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get recent activities for the admin dashboard with sample data."""
    from src.models.market_data_provider import MarketDataProvider, ProviderActivity
    from src.services.dashboard_activity_service import create_sample_activities, get_dashboard_activity_summary

    logger.info(f"Admin user {current_admin.email} requesting dashboard recent activities")

    # Handle reset request or ensure providers exist
    if reset:
        logger.info(f"Reset requested by admin {current_admin.email}, clearing existing activities")
        db.query(ProviderActivity).delete()
        db.commit()

    # Ensure we have providers for real activities
    providers = db.query(MarketDataProvider).all()
    if not providers:
        # Create real providers (not sample)
        yfinance_provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            rate_limit_per_minute=60,
            rate_limit_per_day=60000,
            priority=1
        )
        alpha_provider = MarketDataProvider(
            name="alpha_vantage",
            display_name="Alpha Vantage",
            is_enabled=False,
            rate_limit_per_minute=5,
            rate_limit_per_day=15000,
            priority=2
        )
        db.add_all([yfinance_provider, alpha_provider])
        db.commit()
        logger.info("Created market data providers for live activity tracking")

    # Get recent activities
    from src.services.activity_service import get_recent_activities_all_providers

    activities = get_recent_activities_all_providers(
        db_session=db,
        limit=limit,
        page=1,
        size=limit
    )

    # Get provider display names
    providers = {p.name: p.display_name for p in db.query(MarketDataProvider).all()}

    # Convert to dashboard format with relative time
    dashboard_activities = []
    for activity in activities:
        dashboard_activities.append(DashboardActivity(
            id=str(activity.id),
            provider_id=activity.provider_id,
            provider_name=providers.get(activity.provider_id, activity.provider_id),
            activity_type=activity.activity_type,
            description=activity.description,
            status=activity.status,
            timestamp=to_iso_string(activity.timestamp),
            relative_time=calculate_relative_time(activity.timestamp),
            metadata=activity.activity_metadata
        ))

    # Get activity summary
    summary = get_dashboard_activity_summary(db, hours=24)

    return DashboardActivitiesResponse(
        activities=dashboard_activities,
        summary=summary
    )
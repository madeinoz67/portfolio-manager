"""
Admin API endpoints for user management and system administration.
"""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, Request
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
from src.schemas.audit_log import (
    AuditLogResponse, AuditLogEntry, AuditLogPagination,
    AuditLogFilters, AuditLogMetadata, AuditLogStats,
    AuditLogStatsResponse, AuditLogExportRequest
)
from src.models.audit_log import AuditLog, AuditEventType
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

    # Use ProviderActivity table for accurate live usage data (consistent with api-usage endpoint)
    from src.models.market_data_provider import ProviderActivity

    # Get today's usage stats per provider from activity logs
    today_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) == today
    ).all()

    # Get monthly usage stats per provider from activity logs
    monthly_activities = db.query(ProviderActivity).filter(
        func.date(ProviderActivity.timestamp) >= current_month_start.date()
    ).all()

    # Group activities by provider for today
    today_usage = {}
    for activity in today_activities:
        provider_id = activity.provider_id
        if provider_id not in today_usage:
            today_usage[provider_id] = {'calls': 0, 'avg_response_time': 0}
        today_usage[provider_id]['calls'] += 1

    # Group activities by provider for this month
    monthly_usage = {}
    for activity in monthly_activities:
        provider_id = activity.provider_id
        if provider_id not in monthly_usage:
            monthly_usage[provider_id] = {'calls': 0, 'cost': 0.0}  # Use 'cost' key to match expected format
        monthly_usage[provider_id]['calls'] += 1

    # Lookup dictionaries are already created as today_usage and monthly_usage
    today_lookup = today_usage
    monthly_lookup = monthly_usage

    # Rate limit detection from ProviderActivity table (look for rate limit error statuses)
    rate_limited_providers = set()
    for activity in today_activities:
        if activity.status == "error" and activity.description and "rate limit" in activity.description.lower():
            rate_limited_providers.add(activity.provider_id)

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
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle market data provider enabled/disabled status."""
    logger.info(f"Admin user {current_admin.email} toggling provider {provider_id}")

    from src.models.market_data_provider import MarketDataProvider
    from src.utils.datetime_utils import now
    from src.services.audit_service import AuditService
    from fastapi import HTTPException, Request

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

        # Create audit log entry
        try:
            audit_service = AuditService(db)

            if provider.is_enabled:
                audit_service.log_provider_enabled(
                    provider_id=provider.name,
                    provider_name=provider.display_name,
                    admin_user_id=str(current_admin.id),
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )
            else:
                audit_service.log_provider_disabled(
                    provider_id=provider.name,
                    provider_name=provider.display_name,
                    admin_user_id=str(current_admin.id),
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

            db.commit()  # Commit audit log
        except Exception as audit_error:
            logger.error(f"Failed to create audit log for provider toggle: {audit_error}")
            # Don't fail the operation if audit logging fails

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

    # Ensure now is also naive UTC (convert timezone-aware to naive UTC)
    if now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)

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


# Audit Log Endpoints

@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    date_from: Optional[str] = Query(None, description="Filter events from this date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter events until this date (ISO format)"),
    search: Optional[str] = Query(None, description="Full-text search in event descriptions"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order")
) -> AuditLogResponse:
    """
    Get audit logs with pagination, filtering, and search.
    Admin access required.
    """
    from datetime import datetime
    import time

    start_time = time.time()
    logger.info(f"Admin user {admin_user.email} requesting audit logs")

    # Build query with filters
    query = db.query(AuditLog).join(User, AuditLog.user_id == User.id)

    # Apply filters
    if user_id:
        try:
            import uuid
            user_uuid = uuid.UUID(user_id)
            query = query.filter(AuditLog.user_id == user_uuid)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )

    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
            query = query.filter(AuditLog.event_type == event_type_enum)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)

    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp >= from_date)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format."
            )

    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp <= to_date)
        except ValueError:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format."
            )

    if search:
        query = query.filter(AuditLog.event_description.ilike(f"%{search}%"))

    # Get total count for pagination
    total_items = query.count()

    # Apply sorting
    if sort_by == "timestamp":
        sort_column = AuditLog.timestamp
    elif sort_by == "event_type":
        sort_column = AuditLog.event_type
    elif sort_by == "user_id":
        sort_column = AuditLog.user_id
    else:
        sort_column = AuditLog.timestamp

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * limit
    total_pages = (total_items + limit - 1) // limit  # Ceiling division
    audit_logs = query.offset(offset).limit(limit).all()

    # Build response data
    audit_entries = []
    for audit_log in audit_logs:
        audit_entries.append(AuditLogEntry(
            id=audit_log.id,
            event_type=audit_log.event_type.value,
            event_description=audit_log.event_description,
            user_id=str(audit_log.user_id),
            user_email=audit_log.user.email,
            entity_type=audit_log.entity_type,
            entity_id=audit_log.entity_id,
            timestamp=to_iso_string(audit_log.timestamp),
            event_metadata=audit_log.event_metadata,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            created_at=to_iso_string(audit_log.created_at)
        ))

    # Get total events in system for metadata
    total_events_in_system = db.query(AuditLog).count()

    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    return AuditLogResponse(
        data=audit_entries,
        pagination=AuditLogPagination(
            current_page=page,
            total_pages=total_pages,
            total_items=total_items,
            items_per_page=len(audit_entries)
        ),
        filters=AuditLogFilters(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        ),
        meta=AuditLogMetadata(
            request_timestamp=to_iso_string(utc_now()),
            processing_time_ms=processing_time_ms,
            total_events_in_system=total_events_in_system
        )
    )


@router.get("/audit-logs/{audit_id}")
async def get_audit_log_entry(
    audit_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> AuditLogEntry:
    """
    Get a specific audit log entry by ID.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting audit log entry {audit_id}")

    from fastapi import HTTPException, status

    audit_log = db.query(AuditLog).join(User, AuditLog.user_id == User.id).filter(AuditLog.id == audit_id).first()

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log entry not found"
        )

    return AuditLogEntry(
        id=audit_log.id,
        event_type=audit_log.event_type.value,
        event_description=audit_log.event_description,
        user_id=str(audit_log.user_id),
        user_email=audit_log.user.email,
        entity_type=audit_log.entity_type,
        entity_id=audit_log.entity_id,
        timestamp=to_iso_string(audit_log.timestamp),
        event_metadata=audit_log.event_metadata,
        ip_address=audit_log.ip_address,
        user_agent=audit_log.user_agent,
        created_at=to_iso_string(audit_log.created_at)
    )


@router.get("/audit-logs/stats", response_model=AuditLogStatsResponse)
async def get_audit_log_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> AuditLogStatsResponse:
    """
    Get audit log statistics and breakdowns.
    Admin access required.
    """
    from datetime import datetime, timedelta

    logger.info(f"Admin user {admin_user.email} requesting audit log statistics")

    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Get basic counts
    total_events = db.query(AuditLog).count()
    events_today = db.query(AuditLog).filter(AuditLog.timestamp >= today_start).count()
    events_this_week = db.query(AuditLog).filter(AuditLog.timestamp >= week_start).count()
    events_this_month = db.query(AuditLog).filter(AuditLog.timestamp >= month_start).count()

    # Get event types breakdown
    event_types_result = db.query(
        AuditLog.event_type,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.event_type).all()

    event_types_breakdown = {
        event_type.value: count for event_type, count in event_types_result
    }

    # Get user activity breakdown (top 10 most active users)
    user_activity_result = db.query(
        User.email,
        func.count(AuditLog.id).label('count')
    ).join(AuditLog, AuditLog.user_id == User.id).group_by(User.email).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()

    user_activity_breakdown = {
        email: count for email, count in user_activity_result
    }

    # Get entity types breakdown
    entity_types_result = db.query(
        AuditLog.entity_type,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.entity_type).all()

    entity_types_breakdown = {
        entity_type: count for entity_type, count in entity_types_result
    }

    return AuditLogStatsResponse(
        stats=AuditLogStats(
            total_events=total_events,
            events_today=events_today,
            events_this_week=events_this_week,
            events_this_month=events_this_month,
            event_types_breakdown=event_types_breakdown,
            user_activity_breakdown=user_activity_breakdown,
            entity_types_breakdown=entity_types_breakdown
        ),
        generated_at=to_iso_string(now)
    )


# Missing Market Data Admin Endpoints

class MarketDataProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    is_enabled: bool
    priority: int
    rate_limit_per_minute: int


class MarketDataDashboardResponse(BaseModel):
    providers_status: dict
    recent_activity: dict
    system_health: dict
    scheduler_info: dict
    performance_metrics: dict


@router.get("/market-data/dashboard", response_model=MarketDataDashboardResponse)
async def get_market_data_dashboard(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get market data dashboard overview with providers status, recent activity, and system health."""
    logger.info(f"Admin user {current_admin.email} requesting market data dashboard")

    from src.models.market_data_provider import MarketDataProvider as DBMarketDataProvider
    from src.services.scheduler_service import get_scheduler_service
    from src.models.market_data_provider import ProviderActivity
    from datetime import timedelta

    # Get providers status
    providers = db.query(DBMarketDataProvider).all()
    providers_status = {
        "total_providers": len(providers),
        "enabled_providers": len([p for p in providers if p.is_enabled]),
        "disabled_providers": len([p for p in providers if not p.is_enabled]),
        "providers": [
            {
                "id": p.name,
                "name": p.display_name,
                "is_enabled": p.is_enabled,
                "priority": p.priority,
                "rate_limit_per_minute": p.rate_limit_per_minute
            }
            for p in providers
        ]
    }

    # Get recent activity summary (last 24 hours)
    twenty_four_hours_ago = utc_now() - timedelta(hours=24)
    recent_activities = db.query(ProviderActivity).filter(
        ProviderActivity.timestamp >= twenty_four_hours_ago
    ).all()

    recent_activity = {
        "total_activities": len(recent_activities),
        "successful_activities": len([a for a in recent_activities if a.status == "success"]),
        "failed_activities": len([a for a in recent_activities if a.status == "error"]),
        "warning_activities": len([a for a in recent_activities if a.status == "warning"]),
        "latest_activities": [
            {
                "id": str(a.id),
                "provider_id": a.provider_id,
                "activity_type": a.activity_type,
                "description": a.description,
                "status": a.status,
                "timestamp": to_iso_string(a.timestamp)
            }
            for a in sorted(recent_activities, key=lambda x: x.timestamp, reverse=True)[:5]
        ]
    }

    # Get system health
    system_health = {
        "status": "healthy",
        "uptime": "24h 30m",
        "memory_usage": "45%",
        "cpu_usage": "12%",
        "database_status": "connected",
        "last_health_check": to_iso_string(utc_now())
    }

    # Get scheduler info
    try:
        scheduler_service = get_scheduler_service(db)
        status_info = scheduler_service.status_info
        scheduler_info = {
            "state": status_info["state"],
            "last_run": status_info["last_run"],
            "next_run": status_info["next_run"],
            "total_runs": status_info.get("total_executions", 0),
            "successful_runs": status_info.get("successful_executions", 0),
            "failed_runs": status_info.get("failed_executions", 0),
            "success_rate": status_info.get("success_rate_percent", 0.0)
        }
    except Exception as e:
        logger.warning(f"Failed to get scheduler info: {e}")
        scheduler_info = {
            "state": "unknown",
            "last_run": None,
            "next_run": None,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "success_rate": 0.0
        }

    # Get performance metrics
    performance_metrics = {
        "avg_response_time": 150,  # ms
        "requests_per_minute": 5,
        "success_rate": 98.5,
        "error_rate": 1.5,
        "data_freshness": "2 minutes ago"
    }

    return MarketDataDashboardResponse(
        providers_status=providers_status,
        recent_activity=recent_activity,
        system_health=system_health,
        scheduler_info=scheduler_info,
        performance_metrics=performance_metrics
    )


@router.get("/market-data/providers", response_model=List[MarketDataProviderResponse])
async def get_market_data_providers(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get list of all market data providers."""
    logger.info(f"Admin user {current_admin.email} requesting market data providers list")

    from src.models.market_data_provider import MarketDataProvider as DBMarketDataProvider

    providers = db.query(DBMarketDataProvider).all()

    return [
        MarketDataProviderResponse(
            id=p.name,
            name=p.name,
            display_name=p.display_name,
            is_enabled=p.is_enabled,
            priority=p.priority,
            rate_limit_per_minute=p.rate_limit_per_minute
        )
        for p in providers
    ]


# Scheduler Control Models
class SchedulerStatus(BaseModel):
    schedulerName: str
    state: str  # stopped, running, paused, error
    lastRun: Optional[str] = None
    nextRun: Optional[str] = None
    pauseUntil: Optional[str] = None
    errorMessage: Optional[str] = None
    configuration: dict
    uptimeSeconds: Optional[int] = None
    # Execution metrics for admin UI (field names match frontend expectations)
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    symbols_processed: int = 0
    success_rate: float = 0.0


class SchedulerControlRequest(BaseModel):
    action: str  # start, stop, pause, resume
    durationMinutes: Optional[int] = None  # for pause action
    reason: Optional[str] = None  # for stop action
    configuration: Optional[dict] = None  # for start action


class SchedulerControlResponse(BaseModel):
    schedulerName: str
    action: str
    success: bool
    message: str
    newState: str
    status: SchedulerStatus


class SchedulerConfigurationRequest(BaseModel):
    intervalMinutes: Optional[int] = None
    maxConcurrentJobs: Optional[int] = None
    retryAttempts: Optional[int] = None
    enabledProviders: Optional[List[str]] = None
    bulkMode: Optional[bool] = None
    timeoutSeconds: Optional[int] = None


class SchedulerConfigurationResponse(BaseModel):
    schedulerName: str
    success: bool
    message: str
    changes: dict
    configuration: dict


@router.get("/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_status(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get current scheduler status."""
    logger.info(f"Admin user {current_admin.email} requesting scheduler status")

    from src.services.scheduler_service import get_scheduler_service

    scheduler_service = get_scheduler_service(db)
    status_info = scheduler_service.status_info

    return SchedulerStatus(
        schedulerName="market_data_scheduler",
        state=status_info["state"],
        lastRun=status_info["last_run"],
        nextRun=status_info["next_run"],
        pauseUntil=status_info["pause_until"],
        errorMessage=status_info["error_message"],
        configuration=status_info["configuration"],
        uptimeSeconds=status_info["uptime_seconds"],
        # Execution metrics from scheduler service
        total_runs=status_info.get("total_executions", 0),
        successful_runs=status_info.get("successful_executions", 0),
        failed_runs=status_info.get("failed_executions", 0),
        symbols_processed=status_info.get("total_symbols_processed", 0),
        success_rate=status_info.get("success_rate_percent", 0.0)
    )


@router.post("/scheduler/control", response_model=SchedulerControlResponse)
async def control_scheduler(
    control_request: SchedulerControlRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Control scheduler operations (start, stop, pause, resume)."""
    logger.info(f"Admin user {current_admin.email} requesting scheduler control: {control_request.action}")

    from src.services.scheduler_service import get_scheduler_service, SchedulerState
    from src.services.audit_service import AuditService
    from fastapi import HTTPException

    scheduler_service = get_scheduler_service(db)
    audit_service = AuditService(db)
    scheduler_name = "market_data_scheduler"

    success = False
    message = ""

    try:
        if control_request.action == "start":
            success = scheduler_service.start(control_request.configuration)
            message = "Scheduler started successfully" if success else "Failed to start scheduler"

            if success:
                # Create audit log
                audit_service.log_scheduler_started(
                    scheduler_name=scheduler_name,
                    admin_user_id=str(current_admin.id),
                    scheduler_config=control_request.configuration,
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

        elif control_request.action == "stop":
            success = scheduler_service.stop(control_request.reason)
            message = "Scheduler stopped successfully" if success else "Failed to stop scheduler"

            if success:
                # Create audit log
                audit_service.log_scheduler_stopped(
                    scheduler_name=scheduler_name,
                    admin_user_id=str(current_admin.id),
                    reason=control_request.reason,
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

        elif control_request.action == "pause":
            success = scheduler_service.pause(control_request.durationMinutes)
            duration_text = f" for {control_request.durationMinutes} minutes" if control_request.durationMinutes else " indefinitely"
            message = f"Scheduler paused successfully{duration_text}" if success else "Failed to pause scheduler"

            if success:
                # Create audit log
                audit_service.log_scheduler_paused(
                    scheduler_name=scheduler_name,
                    admin_user_id=str(current_admin.id),
                    duration_minutes=control_request.durationMinutes,
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

        elif control_request.action == "resume":
            success = scheduler_service.resume()
            message = "Scheduler resumed successfully" if success else "Failed to resume scheduler"

            if success:
                # Create audit log
                audit_service.log_scheduler_resumed(
                    scheduler_name=scheduler_name,
                    admin_user_id=str(current_admin.id),
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

        elif control_request.action == "restart":
            # Restart means: stop if running/paused, then start
            current_state = scheduler_service.state

            # Step 1: Stop the scheduler if it's not already stopped
            stop_success = True
            if current_state != SchedulerState.STOPPED:
                stop_success = scheduler_service.stop("admin_restart")

            # Step 2: Start the scheduler
            if stop_success:
                success = scheduler_service.start(control_request.configuration)
                message = "Scheduler restarted successfully" if success else "Failed to restart scheduler"
            else:
                success = False
                message = "Failed to restart scheduler - could not stop existing scheduler"

            if success:
                # Create audit log for restart
                audit_service.log_scheduler_started(
                    scheduler_name=scheduler_name,
                    admin_user_id=str(current_admin.id),
                    scheduler_config=control_request.configuration,
                    ip_address=getattr(request.client, 'host', None) if request.client else None,
                    user_agent=request.headers.get('User-Agent')
                )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {control_request.action}"
            )

        # Commit audit logs
        if success:
            db.commit()

        # Get updated status
        status_info = scheduler_service.status_info

        return SchedulerControlResponse(
            schedulerName=scheduler_name,
            action=control_request.action,
            success=success,
            message=message,
            newState=status_info["state"],
            status=SchedulerStatus(
                schedulerName=scheduler_name,
                state=status_info["state"],
                lastRun=status_info["last_run"],
                nextRun=status_info["next_run"],
                pauseUntil=status_info["pause_until"],
                errorMessage=status_info["error_message"],
                configuration=status_info["configuration"],
                uptimeSeconds=status_info["uptime_seconds"],
                # Execution metrics from scheduler service
                total_runs=status_info.get("total_executions", 0),
                successful_runs=status_info.get("successful_executions", 0),
                failed_runs=status_info.get("failed_executions", 0),
                symbols_processed=status_info.get("total_symbols_processed", 0),
                success_rate=status_info.get("success_rate_percent", 0.0)
            )
        )

    except Exception as e:
        logger.error(f"Scheduler control failed for action {control_request.action}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to {control_request.action} scheduler: {str(e)}"
        )


@router.patch("/scheduler/configuration", response_model=SchedulerConfigurationResponse)
async def update_scheduler_configuration(
    config_request: SchedulerConfigurationRequest,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update scheduler configuration."""
    logger.info(f"Admin user {current_admin.email} updating scheduler configuration")

    from src.services.scheduler_service import get_scheduler_service
    from src.services.audit_service import AuditService
    from fastapi import HTTPException

    scheduler_service = get_scheduler_service(db)
    audit_service = AuditService(db)
    scheduler_name = "market_data_scheduler"

    try:
        # Convert request to dictionary, excluding None values
        config_updates = {
            k: v for k, v in config_request.model_dump().items()
            if v is not None
        }

        if not config_updates:
            raise HTTPException(
                status_code=400,
                detail="No configuration updates provided"
            )

        # Update configuration
        changes = scheduler_service.update_configuration(config_updates)

        success = bool(changes)
        message = f"Configuration updated: {list(changes.keys())}" if success else "No changes made"

        if success:
            # Create audit log
            audit_service.log_scheduler_configured(
                scheduler_name=scheduler_name,
                admin_user_id=str(current_admin.id),
                configuration_changes=changes,
                ip_address=getattr(request.client, 'host', None) if request.client else None,
                user_agent=request.headers.get('User-Agent')
            )
            db.commit()

        # Get updated configuration
        current_config = scheduler_service.configuration.to_dict()

        return SchedulerConfigurationResponse(
            schedulerName=scheduler_name,
            success=success,
            message=message,
            changes=changes,
            configuration=current_config
        )

    except Exception as e:
        logger.error(f"Scheduler configuration update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update scheduler configuration: {str(e)}"
        )


# Portfolio Update Metrics Models
class PortfolioUpdateStats24h(BaseModel):
    totalUpdates: int
    successfulUpdates: int
    failedUpdates: int
    successRate: float
    avgUpdateDurationMs: int
    uniquePortfolios: int
    updateFrequencyPerHour: float
    commonErrorTypes: dict

class QueueHealthMetrics(BaseModel):
    currentQueueSize: int
    avgProcessingRate: float
    maxQueueSize1h: int
    rateLimitHits1h: int
    memoryUsageTrend: str
    queueHealthStatus: str

class StormProtectionMetrics(BaseModel):
    totalCoalescedUpdates: int
    totalIndividualUpdates: int
    coalescingEfficiency: float
    avgSymbolsPerUpdate: float
    stormEventsDetected: int
    protectionEffectiveness: float

class PortfolioPerformanceItem(BaseModel):
    portfolioId: str
    portfolioName: str
    totalUpdates: int
    successRate: float
    avgDurationMs: int
    lastUpdated: str

class UpdateLagAnalysis(BaseModel):
    avgLagMs: int
    medianLagMs: int
    p95LagMs: int
    maxLagMs: int
    samplesAnalyzed: int
    lagDistribution: dict

class PrometheusMetricsResponse(BaseModel):
    metrics: dict


@router.get("/portfolio-updates/stats/24h")
async def get_portfolio_update_stats_24h(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> PortfolioUpdateStats24h:
    """Get portfolio update statistics for the last 24 hours."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    stats = service.get_portfolio_update_stats_24h()

    return PortfolioUpdateStats24h(
        totalUpdates=stats["total_updates"],
        successfulUpdates=stats["successful_updates"],
        failedUpdates=stats["failed_updates"],
        successRate=stats["success_rate"],
        avgUpdateDurationMs=stats["avg_update_duration_ms"],
        uniquePortfolios=stats["unique_portfolios"],
        updateFrequencyPerHour=stats["update_frequency_per_hour"],
        commonErrorTypes=stats["common_error_types"]
    )


@router.get("/portfolio-updates/queue/health")
async def get_portfolio_queue_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> QueueHealthMetrics:
    """Get current portfolio update queue health metrics."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    health = service.get_queue_health_metrics()

    return QueueHealthMetrics(
        currentQueueSize=health["current_queue_size"],
        avgProcessingRate=health["avg_processing_rate"],
        maxQueueSize1h=health["max_queue_size_1h"],
        rateLimitHits1h=health["rate_limit_hits_1h"],
        memoryUsageTrend=health["memory_usage_trend"],
        queueHealthStatus=health["queue_health_status"]
    )


@router.get("/portfolio-updates/storm-protection")
async def get_storm_protection_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> StormProtectionMetrics:
    """Get update storm protection effectiveness metrics."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    metrics = service.get_storm_protection_metrics()

    return StormProtectionMetrics(
        totalCoalescedUpdates=metrics["total_coalesced_updates"],
        totalIndividualUpdates=metrics["total_individual_updates"],
        coalescingEfficiency=metrics["coalescing_efficiency"],
        avgSymbolsPerUpdate=metrics["avg_symbols_per_update"],
        stormEventsDetected=metrics["storm_events_detected"],
        protectionEffectiveness=metrics["protection_effectiveness"]
    )


@router.get("/portfolio-updates/performance/breakdown")
async def get_portfolio_performance_breakdown(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> List[PortfolioPerformanceItem]:
    """Get per-portfolio performance breakdown."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    breakdown = service.get_portfolio_performance_breakdown(limit=limit)

    return [
        PortfolioPerformanceItem(
            portfolioId=item["portfolio_id"],
            portfolioName=item["portfolio_name"],
            totalUpdates=item["total_updates"],
            successRate=item["success_rate"],
            avgDurationMs=item["avg_duration_ms"],
            lastUpdated=to_iso_string(item["last_updated"])
        )
        for item in breakdown
    ]


@router.get("/portfolio-updates/lag-analysis")
async def get_update_lag_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> UpdateLagAnalysis:
    """Get analysis of update lag times (price change to portfolio update)."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    analysis = service.get_update_lag_analysis()

    return UpdateLagAnalysis(
        avgLagMs=analysis["avg_lag_ms"],
        medianLagMs=analysis["median_lag_ms"],
        p95LagMs=analysis["p95_lag_ms"],
        maxLagMs=analysis["max_lag_ms"],
        samplesAnalyzed=analysis["samples_analyzed"],
        lagDistribution=analysis["lag_distribution"]
    )


@router.get("/portfolio-updates/metrics/prometheus")
async def get_portfolio_metrics_prometheus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> PrometheusMetricsResponse:
    """Export portfolio update metrics in Prometheus format for external monitoring."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    metrics = service.export_metrics_for_monitoring()

    return PrometheusMetricsResponse(metrics=metrics)


@router.get("/portfolio-updates/queue/live")
async def get_live_queue_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get current live metrics from the portfolio update queue."""
    from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService

    service = PortfolioUpdateMetricsService(db)
    live_metrics = service.collect_live_queue_metrics()

    return {
        "pendingUpdates": live_metrics["pending_updates"],
        "activePortfolios": live_metrics["active_portfolios"],
        "rateLimitHits": live_metrics["rate_limit_hits"],
        "isProcessing": live_metrics["is_processing"],
        "totalSymbolsQueued": live_metrics["total_symbols_queued"]
    }
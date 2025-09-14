"""
Admin API endpoints for user management and system administration.
"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from src.core.dependencies import get_current_admin_user, get_db
from src.core.logging import get_logger
from src.models.user import User
from src.models.user_role import UserRole
from src.models.portfolio import Portfolio
from src.models.api_usage_metrics import ApiUsageMetrics
from src.schemas.auth import UserResponse

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
            createdAt=user.created_at.isoformat(),
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
            lastUpdated=portfolio.updated_at.isoformat()
        ))

    return AdminUserDetails(
        id=str(user.id),
        email=user.email,
        firstName=user.first_name,
        lastName=user.last_name,
        role=user.role.value,
        isActive=user.is_active,
        createdAt=user.created_at.isoformat() + "Z",
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
        lastUpdated=datetime.now().isoformat()
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

        provider_list.append({
            "providerId": provider.name,
            "providerName": provider.display_name,
            "isEnabled": provider.is_enabled,
            "lastUpdate": provider.updated_at.isoformat(),
            "apiCallsToday": calls_today,
            "monthlyLimit": provider.rate_limit_per_day * 30,  # Approximate monthly limit
            "monthlyUsage": calls_this_month,
            "costPerCall": round(cost_per_call, 4),
            "status": status,
            "avgResponseTimeMs": avg_response_time
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

    from src.models.api_usage_metrics import ApiUsageMetrics
    from sqlalchemy import func, extract
    from datetime import datetime, date

    today = date.today()
    current_month_start = datetime(today.year, today.month, 1)

    # Get today's total requests by summing requests_count
    today_metrics = db.query(
        func.sum(ApiUsageMetrics.requests_count).label('total_requests'),
        func.sum(ApiUsageMetrics.error_count).label('total_errors')
    ).filter(
        func.date(ApiUsageMetrics.recorded_at) == today
    ).first()

    # Get this month's total requests
    month_metrics = db.query(
        func.sum(ApiUsageMetrics.requests_count).label('total_requests')
    ).filter(
        ApiUsageMetrics.recorded_at >= current_month_start
    ).first()

    # Calculate summary statistics
    total_requests_today = int(today_metrics.total_requests or 0)
    total_errors_today = int(today_metrics.total_errors or 0)
    total_requests_this_month = int(month_metrics.total_requests or 0)

    # Calculate success rate
    if total_requests_today > 0:
        success_rate_today = ((total_requests_today - total_errors_today) / total_requests_today) * 100
    else:
        success_rate_today = 0.0

    # Get by provider statistics
    provider_stats = db.query(
        ApiUsageMetrics.provider_id,
        func.sum(ApiUsageMetrics.requests_count).label('requests_today'),
        func.sum(ApiUsageMetrics.error_count).label('errors_today')
    ).filter(
        func.date(ApiUsageMetrics.recorded_at) == today
    ).group_by(ApiUsageMetrics.provider_id).all()

    # Get monthly stats by provider
    monthly_provider_stats = db.query(
        ApiUsageMetrics.provider_id,
        func.sum(ApiUsageMetrics.requests_count).label('requests_this_month')
    ).filter(
        ApiUsageMetrics.recorded_at >= current_month_start
    ).group_by(ApiUsageMetrics.provider_id).all()

    # Create monthly lookup dict
    monthly_lookup = {stat.provider_id: stat.requests_this_month for stat in monthly_provider_stats}

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
    yesterday = current_month_start.replace(day=today.day - 1) if today.day > 1 else None
    daily_change_percent = 0.0

    if yesterday:
        yesterday_metrics = db.query(
            func.sum(ApiUsageMetrics.requests_count).label('total_requests_yesterday')
        ).filter(
            func.date(ApiUsageMetrics.recorded_at) == yesterday.date()
        ).first()

        total_requests_yesterday = int(yesterday_metrics.total_requests_yesterday or 0)

        if total_requests_yesterday > 0:
            daily_change_percent = ((total_requests_today - total_requests_yesterday) / total_requests_yesterday) * 100

    # Calculate weekly change (simplified as month vs last 7 days)
    week_ago = current_month_start.replace(day=max(1, today.day - 7))
    weekly_metrics = db.query(
        func.sum(ApiUsageMetrics.requests_count).label('total_requests_week_ago')
    ).filter(
        ApiUsageMetrics.recorded_at >= week_ago,
        ApiUsageMetrics.recorded_at < current_month_start.replace(day=today.day)
    ).first()

    weekly_change_count = total_requests_today - int(weekly_metrics.total_requests_week_ago or 0)

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
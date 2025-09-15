"""
Service layer for managing provider activity logs.
Handles logging, retrieval, and cleanup of market data provider activities.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Union, Any, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models.market_data_provider import ProviderActivity, MarketDataProvider


def serialize_metadata_for_json(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize metadata to be JSON-compatible by converting problematic types.

    Handles:
    - Decimal objects -> float
    - datetime objects -> ISO string
    - Nested dictionaries recursively

    Args:
        metadata: Dictionary containing metadata that may have non-JSON types

    Returns:
        JSON-serializable dictionary
    """
    if not metadata:
        return {}

    def convert_value(value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [convert_value(item) for item in value]
        else:
            return value

    return {key: convert_value(value) for key, value in metadata.items()}


def log_provider_activity(
    db_session: Session,
    provider_id: str,
    activity_type: str,
    description: str,
    status: str,
    metadata: Optional[dict] = None,
    timestamp: Optional[datetime] = None
) -> ProviderActivity:
    """
    Log a new provider activity.

    Args:
        db_session: Database session
        provider_id: ID of the market data provider
        activity_type: Type of activity (API_CALL, RATE_LIMIT, API_ERROR, etc.)
        description: Human-readable description of the activity
        status: Status of the activity (success, error, warning)
        metadata: Optional additional context data
        timestamp: Optional custom timestamp (defaults to current time)

    Returns:
        The created ProviderActivity instance
    """
    # Serialize metadata to ensure JSON compatibility
    serialized_metadata = serialize_metadata_for_json(metadata or {})

    activity = ProviderActivity(
        provider_id=provider_id,
        activity_type=activity_type,
        description=description,
        status=status,
        activity_metadata=serialized_metadata
    )

    # Set custom timestamp if provided
    if timestamp is not None:
        activity.timestamp = timestamp

    db_session.add(activity)
    db_session.commit()
    return activity


def get_recent_activities(
    db_session: Session,
    provider_id: str,
    limit: int = 10,
    status_filter: Optional[str] = None
) -> List[ProviderActivity]:
    """
    Get recent activities for a specific provider.

    Args:
        db_session: Database session
        provider_id: ID of the market data provider
        limit: Maximum number of activities to return
        status_filter: Optional status filter ('success', 'error', 'warning')

    Returns:
        List of ProviderActivity instances, ordered by timestamp (newest first)
    """
    query = db_session.query(ProviderActivity).filter(
        ProviderActivity.provider_id == provider_id
    )

    if status_filter:
        query = query.filter(ProviderActivity.status == status_filter)

    return query.order_by(desc(ProviderActivity.timestamp)).limit(limit).all()


def get_recent_activities_all_providers(
    db_session: Session,
    limit: int = 50,
    provider_filter: Optional[Union[str, List[str]]] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20
) -> List[ProviderActivity]:
    """
    Get recent activities across all or filtered providers.

    Args:
        db_session: Database session
        limit: Maximum number of activities to return
        provider_filter: Single provider ID or list of provider IDs to filter by
        status_filter: Optional status filter ('success', 'error', 'warning')
        page: Page number for pagination (1-based)
        size: Number of items per page

    Returns:
        List of ProviderActivity instances, ordered by timestamp (newest first)
    """
    query = db_session.query(ProviderActivity)

    # Apply provider filter
    if provider_filter:
        if isinstance(provider_filter, str):
            query = query.filter(ProviderActivity.provider_id == provider_filter)
        elif isinstance(provider_filter, list):
            query = query.filter(ProviderActivity.provider_id.in_(provider_filter))

    # Apply status filter
    if status_filter:
        query = query.filter(ProviderActivity.status == status_filter)

    # Calculate offset for pagination
    offset = (page - 1) * size

    return query.order_by(desc(ProviderActivity.timestamp)).offset(offset).limit(size).all()


def cleanup_old_activities(
    db_session: Session,
    days_to_keep: int = 30
) -> int:
    """
    Clean up old activity records to prevent database bloat.

    Args:
        db_session: Database session
        days_to_keep: Number of days worth of activities to keep

    Returns:
        Number of records deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

    deleted_count = db_session.query(ProviderActivity).filter(
        ProviderActivity.timestamp < cutoff_date
    ).count()

    db_session.query(ProviderActivity).filter(
        ProviderActivity.timestamp < cutoff_date
    ).delete()

    db_session.commit()
    return deleted_count


def get_activity_summary_for_provider(
    db_session: Session,
    provider_id: str,
    hours: int = 24
) -> dict:
    """
    Get activity summary statistics for a provider.

    Args:
        db_session: Database session
        provider_id: ID of the market data provider
        hours: Number of hours to look back

    Returns:
        Dictionary containing activity counts by status
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    activities = db_session.query(ProviderActivity).filter(
        ProviderActivity.provider_id == provider_id,
        ProviderActivity.timestamp >= since
    ).all()

    summary = {
        'total': len(activities),
        'success': len([a for a in activities if a.status == 'success']),
        'error': len([a for a in activities if a.status == 'error']),
        'warning': len([a for a in activities if a.status == 'warning']),
        'last_activity': activities[0].timestamp if activities else None
    }

    return summary
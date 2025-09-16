"""
Dashboard activity service for creating realistic activity logging.

Provides functions to log different types of market data provider activities
that will be displayed in the admin dashboard recent activity feed.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from src.services.activity_service import log_provider_activity
from src.utils.datetime_utils import to_iso_string


def log_bulk_price_update(
    db_session: Session,
    provider_id: str,
    symbols_count: int,
    duration_ms: Optional[int] = None,
    success_rate: Optional[float] = None
) -> None:
    """Log a successful bulk price update activity."""
    metadata = {"symbols_count": symbols_count}
    if duration_ms is not None:
        metadata["duration_ms"] = duration_ms
    if success_rate is not None:
        metadata["success_rate"] = success_rate

    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="BULK_PRICE_UPDATE",
        description=f"Successfully updated prices for {symbols_count} symbols",
        status="success",
        metadata=metadata
    )


def log_batch_update_completed(
    db_session: Session,
    provider_id: str,
    batch_type: str = "S&P 500 stocks",
    batch_size: Optional[int] = None,
    success_rate: Optional[float] = None
) -> None:
    """Log a completed batch update activity."""
    metadata = {}
    if batch_size is not None:
        metadata["batch_size"] = batch_size
    if success_rate is not None:
        metadata["success_rate"] = success_rate

    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="BATCH_UPDATE",
        description=f"Batch price update completed for {batch_type}",
        status="success",
        metadata=metadata
    )


def log_provider_switch(
    db_session: Session,
    provider_id: str,
    reason: str = "rate_limit_exceeded",
    backup_provider: Optional[str] = None
) -> None:
    """Log when switching to backup provider due to issues."""
    metadata = {"reason": reason}
    if backup_provider:
        metadata["backup_provider"] = backup_provider

    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="PROVIDER_SWITCH",
        description="Switched to backup provider due to rate limiting",
        status="warning",
        metadata=metadata
    )


def log_error_threshold_detected(
    db_session: Session,
    provider_id: str,
    error_rate: float,
    new_interval_sec: int
) -> None:
    """Log when high error rate is detected and retry intervals are increased."""
    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="ERROR_THRESHOLD",
        description="High error rate detected, increased retry intervals",
        status="warning",
        metadata={
            "error_rate": error_rate,
            "new_interval_sec": new_interval_sec
        }
    )


def log_rate_limit_reset(
    db_session: Session,
    providers_reset: List[str]
) -> None:
    """Log when daily rate limits are reset for providers."""
    log_provider_activity(
        db_session=db_session,
        provider_id="system",
        activity_type="RATE_LIMIT_RESET",
        description="Daily rate limits reset for all providers",
        status="info",
        metadata={"providers_reset": providers_reset}
    )


def log_api_key_validation(
    db_session: Session,
    provider_id: str,
    is_valid: bool,
    error_message: Optional[str] = None
) -> None:
    """Log API key validation results."""
    if is_valid:
        log_provider_activity(
            db_session=db_session,
            provider_id=provider_id,
            activity_type="API_KEY_VALIDATION",
            description="API key validation successful",
            status="success",
            metadata={"validation_result": "valid"}
        )
    else:
        log_provider_activity(
            db_session=db_session,
            provider_id=provider_id,
            activity_type="API_KEY_VALIDATION",
            description=f"API key validation failed: {error_message or 'Invalid key'}",
            status="error",
            metadata={
                "validation_result": "invalid",
                "error_message": error_message
            }
        )


def log_connection_timeout(
    db_session: Session,
    provider_id: str,
    timeout_duration_sec: int,
    retry_count: int = 0
) -> None:
    """Log connection timeout events."""
    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="CONNECTION_TIMEOUT",
        description=f"Connection timeout after {timeout_duration_sec}s, retry #{retry_count}",
        status="error",
        metadata={
            "timeout_duration_sec": timeout_duration_sec,
            "retry_count": retry_count
        }
    )


def log_quota_exceeded(
    db_session: Session,
    provider_id: str,
    quota_type: str = "daily",
    limit_value: Optional[int] = None
) -> None:
    """Log when API quota is exceeded."""
    description = f"API {quota_type} quota exceeded"
    if limit_value:
        description += f" ({limit_value} requests)"

    log_provider_activity(
        db_session=db_session,
        provider_id=provider_id,
        activity_type="QUOTA_EXCEEDED",
        description=description,
        status="error",
        metadata={
            "quota_type": quota_type,
            "limit_value": limit_value
        }
    )


def create_sample_activities(db_session: Session) -> None:
    """Create sample activities for testing the admin dashboard."""
    now = datetime.utcnow()

    # Create activities that match the UI design examples
    sample_activities = [
        # Recent success - 2 minutes ago
        {
            "function": log_bulk_price_update,
            "args": {
                "provider_id": "alpha_vantage",
                "symbols_count": 25,
                "duration_ms": 3420
            },
            "timestamp_offset": timedelta(minutes=2)
        },

        # Batch update - 15 minutes ago
        {
            "function": log_batch_update_completed,
            "args": {
                "provider_id": "yfinance",
                "batch_type": "S&P 500 stocks",
                "batch_size": 500,
                "success_rate": 0.98
            },
            "timestamp_offset": timedelta(minutes=15)
        },

        # Provider switch warning - 1 hour ago
        {
            "function": log_provider_switch,
            "args": {
                "provider_id": "alpha_vantage",
                "reason": "rate_limit_exceeded",
                "backup_provider": "yfinance"
            },
            "timestamp_offset": timedelta(hours=1)
        },

        # Error threshold - 3 hours ago
        {
            "function": log_error_threshold_detected,
            "args": {
                "provider_id": "yfinance",
                "error_rate": 0.15,
                "new_interval_sec": 300
            },
            "timestamp_offset": timedelta(hours=3)
        },

        # Daily reset - 6 hours ago
        {
            "function": log_rate_limit_reset,
            "args": {
                "providers_reset": ["yfinance", "alpha_vantage"]
            },
            "timestamp_offset": timedelta(hours=6)
        },

        # API key validation error - 8 hours ago
        {
            "function": log_api_key_validation,
            "args": {
                "provider_id": "alpha_vantage",
                "is_valid": False,
                "error_message": "Invalid or expired API key"
            },
            "timestamp_offset": timedelta(hours=8)
        },

        # Connection timeout - 12 hours ago
        {
            "function": log_connection_timeout,
            "args": {
                "provider_id": "yfinance",
                "timeout_duration_sec": 30,
                "retry_count": 3
            },
            "timestamp_offset": timedelta(hours=12)
        }
    ]

    # Log each activity with the appropriate timestamp
    for activity_data in sample_activities:
        # Calculate the historical timestamp
        historical_timestamp = now - activity_data["timestamp_offset"]

        # Call the logging function but we need to use log_provider_activity directly
        # to set the custom timestamp
        function_name = activity_data["function"].__name__
        args = activity_data["args"]

        if function_name == "log_bulk_price_update":
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="BULK_PRICE_UPDATE",
                description=f"Successfully updated prices for {args['symbols_count']} symbols",
                status="success",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )
        elif function_name == "log_batch_update_completed":
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="BATCH_UPDATE",
                description=f"Batch price update completed for {args.get('batch_type', 'stocks')}",
                status="success",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )
        elif function_name == "log_provider_switch":
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="PROVIDER_SWITCH",
                description=f"Switched to backup provider due to {args.get('reason', 'rate limiting')}",
                status="warning",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )
        elif function_name == "log_error_threshold_detected":
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="ERROR_THRESHOLD",
                description=f"High error rate detected, increased retry intervals",
                status="warning",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )
        elif function_name == "log_rate_limit_reset":
            log_provider_activity(
                db_session=db_session,
                provider_id="system",
                activity_type="RATE_LIMIT_RESET",
                description="Daily rate limits reset for all providers",
                status="info",
                metadata=args,
                timestamp=historical_timestamp
            )
        elif function_name == "log_api_key_validation":
            error_msg = args.get("error_message", "Invalid key")
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="API_KEY_VALIDATION",
                description=f"API key validation failed: {error_msg}",
                status="error",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )
        elif function_name == "log_connection_timeout":
            timeout_sec = args.get("timeout_duration_sec", 30)
            retry_count = args.get("retry_count", 0)
            log_provider_activity(
                db_session=db_session,
                provider_id=args["provider_id"],
                activity_type="CONNECTION_TIMEOUT",
                description=f"Connection timeout after {timeout_sec}s, retry #{retry_count}",
                status="error",
                metadata={k: v for k, v in args.items() if k != "provider_id"},
                timestamp=historical_timestamp
            )


def get_dashboard_activity_summary(
    db_session: Session,
    hours: int = 24
) -> Dict:
    """Get activity summary for dashboard widgets."""
    from src.services.activity_service import get_recent_activities_all_providers

    activities = get_recent_activities_all_providers(
        db_session=db_session,
        limit=100  # Get enough activities for summary
    )

    # Filter activities within the time range
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_activities = [
        a for a in activities
        if a.timestamp >= cutoff_time
    ]

    # Calculate summary statistics
    summary = {
        "total_activities": len(recent_activities),
        "by_status": {
            "success": len([a for a in recent_activities if a.status == "success"]),
            "warning": len([a for a in recent_activities if a.status == "warning"]),
            "error": len([a for a in recent_activities if a.status == "error"]),
            "info": len([a for a in recent_activities if a.status == "info"])
        },
        "by_provider": {},
        "activity_types": {},
        "last_updated": to_iso_string(datetime.now(timezone.utc))
    }

    # Count by provider
    for activity in recent_activities:
        provider = activity.provider_id
        summary["by_provider"][provider] = summary["by_provider"].get(provider, 0) + 1

    # Count by activity type
    for activity in recent_activities:
        activity_type = activity.activity_type
        summary["activity_types"][activity_type] = summary["activity_types"].get(activity_type, 0) + 1

    return summary
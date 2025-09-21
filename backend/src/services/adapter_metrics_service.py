"""
Adapter metrics service for admin API integration.

Provides a bridge between the adapter-based metrics system and the admin API,
translating adapter metrics to the admin interface format.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from src.services.adapters.registry import get_provider_registry
from src.services.adapters.metrics import get_metrics_collector
from src.models.market_data_usage_metrics import MarketDataUsageMetrics
from src.models.provider_configuration import ProviderConfiguration
from src.utils.datetime_utils import to_iso_string
from sqlalchemy import text

logger = logging.getLogger(__name__)


class AdapterMetricsService:
    """
    Service to retrieve metrics from adapters for admin interface.

    This service acts as a bridge between the adapter metrics system
    and the admin API, providing unified metrics collection.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.registry = get_provider_registry()
        self.metrics_collector = get_metrics_collector()

    async def get_adapter_metrics(self, adapter_id: Union[str, UUID], time_range: str = "24h") -> Optional[Dict[str, Any]]:
        """
        Get comprehensive metrics for a specific adapter.

        Args:
            adapter_id: Provider configuration ID
            time_range: Time range for metrics (1h, 24h, 7d, 30d)

        Returns:
            Dictionary with adapter metrics or None if not found
        """
        # Get provider configuration
        try:
            # Convert to string and normalize format (remove hyphens for SQLite compatibility)
            adapter_id_str = str(adapter_id).replace('-', '')
            logger.info(f"Looking up adapter configuration for ID: {adapter_id_str}")

            # Query using raw SQL to avoid UUID type conversion issues in SQLite
            config = self.db_session.query(ProviderConfiguration).filter(
                text("provider_configurations.id = :id")
            ).params(id=adapter_id_str).first()
        except Exception as e:
            logger.error(f"Error querying provider configuration for {adapter_id}: {e}")
            return None

        if not config:
            logger.warning(f"Provider configuration not found: {adapter_id_str}")
            return None

        provider_name = config.provider_name

        # Get live metrics from the metrics collector
        live_metrics = self.metrics_collector.get_provider_metrics_snapshot(provider_name)

        # Get historical metrics from database
        db_metrics = self._get_database_metrics(provider_name, time_range)

        # Get adapter instance for additional info
        adapter_instance = await self.registry.get_provider_instance(provider_name)

        # Combine live and historical metrics
        combined_metrics = self._combine_metrics(
            config, live_metrics, db_metrics, adapter_instance
        )

        return combined_metrics

    def _get_database_metrics(self, provider_name: str, time_range: str) -> Dict[str, Any]:
        """Get aggregated metrics from database for the specified time range."""
        try:
            # Calculate time range
            now = datetime.now(timezone.utc)
            hours_back = {
                "1h": 1,
                "24h": 24,
                "7d": 24 * 7,
                "30d": 24 * 30
            }.get(time_range, 24)

            start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours_back)

            # Query aggregated metrics
            metrics_query = self.db_session.query(MarketDataUsageMetrics).filter(
                MarketDataUsageMetrics.provider_name == provider_name,
                MarketDataUsageMetrics.recorded_at >= start_time
            )

            metrics_records = metrics_query.all()

            if not metrics_records:
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "success_rate": 0.0,
                    "average_response_time_ms": 0.0,
                    "total_cost": 0.0,
                    "requests_today": 0,
                    "requests_this_hour": 0,
                    "uptime_percentage": 100.0,
                    "rate_limit_hits": 0,
                    "error_rate_24h": 0.0,
                    "p95_response_time_ms": 0.0,
                    "daily_cost": 0.0,
                    "monthly_cost_estimate": 0.0,
                    "last_request_at": None,
                    "last_success_at": None,
                    "last_failure_at": None
                }

            # Aggregate the metrics (using actual model field names)
            total_requests = sum(m.requests_count or 0 for m in metrics_records)
            successful_requests = sum((m.requests_count or 0) - (m.error_count or 0) for m in metrics_records)  # Calculate from total - errors
            failed_requests = sum(m.error_count or 0 for m in metrics_records)
            total_response_time = sum(float(m.avg_response_time_ms or 0) * (m.requests_count or 0) for m in metrics_records)
            total_cost = sum(float(m.cost_estimate or 0) for m in metrics_records)

            # Calculate derived metrics
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0.0
            average_response_time_ms = (total_response_time / total_requests) if total_requests > 0 else 0.0
            error_rate_24h = (failed_requests / total_requests * 100) if total_requests > 0 else 0.0

            # Get latest timestamps
            sorted_records = sorted(metrics_records, key=lambda x: x.recorded_at, reverse=True)
            last_request_at = sorted_records[0].recorded_at if sorted_records else None

            # Find last success and failure
            last_success_at = None
            last_failure_at = None

            for record in sorted_records:
                if (record.requests_count or 0) > (record.error_count or 0) and not last_success_at:
                    last_success_at = record.recorded_at
                if record.error_count and record.error_count > 0 and not last_failure_at:
                    last_failure_at = record.recorded_at
                if last_success_at and last_failure_at:
                    break

            # Calculate time-specific metrics
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hour_start = now.replace(minute=0, second=0, microsecond=0)

            requests_today = sum(
                m.requests_count or 0 for m in metrics_records
                if (m.recorded_at.replace(tzinfo=timezone.utc) if m.recorded_at.tzinfo is None else m.recorded_at) >= today_start
            )
            requests_this_hour = sum(
                m.requests_count or 0 for m in metrics_records
                if (m.recorded_at.replace(tzinfo=timezone.utc) if m.recorded_at.tzinfo is None else m.recorded_at) >= hour_start
            )

            # Estimate daily and monthly costs
            daily_cost = sum(
                float(m.cost_estimate or 0) for m in metrics_records
                if (m.recorded_at.replace(tzinfo=timezone.utc) if m.recorded_at.tzinfo is None else m.recorded_at) >= today_start
            )
            monthly_cost_estimate = daily_cost * 30

            # Calculate uptime (simplified - assume uptime if recent successful requests)
            recent_successful = any(
                (m.requests_count or 0) > (m.error_count or 0) for m in metrics_records[-10:]  # Last 10 records
            )
            uptime_percentage = 100.0 if recent_successful else 90.0

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate,
                "average_response_time_ms": average_response_time_ms,
                "total_cost": total_cost,
                "requests_today": requests_today,
                "requests_this_hour": requests_this_hour,
                "uptime_percentage": uptime_percentage,
                "rate_limit_hits": 0,  # Would need to track this separately
                "error_rate_24h": error_rate_24h,
                "p95_response_time_ms": 0.0,  # Would need percentile calculation
                "daily_cost": daily_cost,
                "monthly_cost_estimate": monthly_cost_estimate,
                "last_request_at": to_iso_string(last_request_at) if last_request_at else None,
                "last_success_at": to_iso_string(last_success_at) if last_success_at else None,
                "last_failure_at": to_iso_string(last_failure_at) if last_failure_at else None
            }

        except Exception as e:
            logger.error(f"Error getting database metrics for {provider_name}: {e}")
            return {}

    def _combine_metrics(
        self,
        config: ProviderConfiguration,
        live_metrics: Optional[Any],
        db_metrics: Dict[str, Any],
        adapter_instance: Optional[Any]
    ) -> Dict[str, Any]:
        """Combine live metrics, database metrics, and adapter info into new schema format."""
        from datetime import datetime, timezone
        from decimal import Decimal

        # Combine live and database metrics for current metrics
        total_requests = db_metrics.get("total_requests", 0)
        successful_requests = db_metrics.get("successful_requests", 0)
        failed_requests = db_metrics.get("failed_requests", 0)
        avg_response_time_ms = db_metrics.get("average_response_time_ms", 0.0)
        p95_response_time_ms = db_metrics.get("p95_response_time_ms", 0.0)

        # Update with live metrics if available
        if live_metrics:
            total_requests = live_metrics.request_count
            successful_requests = live_metrics.success_count
            failed_requests = live_metrics.error_count
            avg_response_time_ms = live_metrics.avg_latency_ms
            if hasattr(live_metrics, 'response_time_p95') and live_metrics.response_time_p95:
                p95_response_time_ms = live_metrics.response_time_p95

        # Calculate success rate
        success_rate = (successful_requests / total_requests) if total_requests > 0 else 0.0

        # Determine adapter status
        current_status = self._determine_adapter_status(db_metrics, adapter_instance)
        is_healthy = current_status == "healthy"

        # Build current metrics object
        current_metrics = {
            "adapter_id": str(config.id),
            "provider_name": config.provider_name,
            "is_healthy": is_healthy,
            "is_active": config.is_active,
            "last_check": datetime.now(timezone.utc),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "avg_latency_ms": avg_response_time_ms,
            "min_latency_ms": 0.0,  # TODO: Track min latency
            "max_latency_ms": 0.0,  # TODO: Track max latency
            "p95_latency_ms": p95_response_time_ms,
            "requests_per_minute": 0.0,  # TODO: Calculate from recent data
            "rate_limit_remaining": None,
            "rate_limit_reset_time": None,
            "error_count_24h": db_metrics.get("failed_requests", 0),
            "last_error": None,
            "last_error_time": None,
            "circuit_breaker_state": "closed",
            "circuit_breaker_failure_count": 0,
            "circuit_breaker_next_attempt": None
        }

        # Build cost metrics object
        daily_cost = Decimal(str(db_metrics.get("daily_cost", 0.0)))
        monthly_cost_estimate = Decimal(str(db_metrics.get("monthly_cost_estimate", 0.0)))
        cost_per_request = Decimal('0.00')
        if total_requests > 0:
            cost_per_request = daily_cost / Decimal(str(total_requests))

        cost_metrics = {
            "daily_cost": daily_cost,
            "daily_budget": None,
            "daily_budget_used_percent": 0.0,
            "monthly_cost": monthly_cost_estimate,
            "monthly_budget": None,
            "monthly_budget_used_percent": 0.0,
            "cost_per_request": cost_per_request,
            "cost_per_successful_request": cost_per_request,
            "budget_status": "ok",
            "budget_remaining_daily": None,
            "budget_remaining_monthly": None,
            "cost_alerts": [],
            "projected_daily_cost": None,
            "projected_monthly_cost": None
        }

        # Return structured response matching AdapterMetricsResponse schema
        return {
            "adapter_id": str(config.id),
            "provider_name": config.provider_name,
            "current_metrics": current_metrics,
            "cost_metrics": cost_metrics,
            "historical_data": None,  # TODO: Convert db_metrics to historical data points
            "active_alerts": [],
            "last_updated": datetime.now(timezone.utc)
        }

    def _determine_adapter_status(self, metrics: Dict[str, Any], adapter_instance: Optional[Any]) -> str:
        """Determine the current status of an adapter based on metrics."""

        # If no recent requests, status is unknown
        if metrics.get("total_requests", 0) == 0:
            return "healthy"  # Default to healthy for new adapters

        # Check error rate
        error_rate = metrics.get("error_rate_24h", 0)
        success_rate = metrics.get("success_rate", 100)

        if error_rate > 50 or success_rate < 50:
            return "down"
        elif error_rate > 10 or success_rate < 90:
            return "degraded"
        else:
            return "healthy"

    async def get_all_adapter_metrics(self, time_range: str = "24h") -> List[Dict[str, Any]]:
        """
        Get metrics for all configured adapters.

        Args:
            time_range: Time range for metrics

        Returns:
            List of adapter metrics dictionaries
        """
        # Get all active provider configurations
        configs = self.db_session.query(ProviderConfiguration).filter(
            ProviderConfiguration.is_active == True
        ).all()

        metrics_list = []
        for config in configs:
            adapter_metrics = await self.get_adapter_metrics(str(config.id), time_range)
            if adapter_metrics:
                metrics_list.append(adapter_metrics)

        return metrics_list

    async def get_adapter_health_status(self, adapter_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get health status for a specific adapter.

        Args:
            adapter_id: Provider configuration ID

        Returns:
            Health status information
        """
        try:
            # Convert to string and normalize format (remove hyphens for SQLite compatibility)
            adapter_id_str = str(adapter_id).replace('-', '')

            # Query using raw SQL to avoid UUID type conversion issues in SQLite
            config = self.db_session.query(ProviderConfiguration).filter(
                text("provider_configurations.id = :id")
            ).params(id=adapter_id_str).first()
        except Exception as e:
            logger.error(f"Error querying provider configuration for {adapter_id}: {e}")
            return None

        if not config:
            return None

        # Get adapter instance and perform health check
        adapter_instance = await self.registry.get_provider_instance(config.provider_name)

        if not adapter_instance:
            # Try to create instance
            adapter_instance = await self.registry.create_provider_instance(
                config.provider_name,
                config.config_data
            )

        health_status = {
            "adapter_id": adapter_id_str,
            "provider_name": config.provider_name,
            "display_name": config.display_name,
            "is_healthy": False,
            "last_health_check": datetime.now(timezone.utc).isoformat(),
            "health_check_response_time_ms": 0,
            "error_message": None,
            "capabilities": None
        }

        if adapter_instance:
            try:
                # Perform health check
                health_response = await adapter_instance.health_check()

                health_status.update({
                    "is_healthy": health_response.success,
                    "health_check_response_time_ms": health_response.response_time_ms or 0,
                    "error_message": health_response.error_message if not health_response.success else None,
                    "capabilities": {
                        "supports_real_time": adapter_instance.capabilities.supports_real_time,
                        "supports_historical": adapter_instance.capabilities.supports_historical,
                        "supports_bulk_quotes": adapter_instance.capabilities.supports_bulk_quotes,
                        "max_symbols_per_request": adapter_instance.capabilities.max_symbols_per_request,
                        "rate_limit_per_minute": adapter_instance.capabilities.rate_limit_per_minute,
                        "cost_model": adapter_instance.cost_info.cost_model
                    }
                })

            except Exception as e:
                health_status.update({
                    "is_healthy": False,
                    "error_message": f"Health check failed: {str(e)}"
                })
        else:
            health_status.update({
                "error_message": "Unable to create adapter instance"
            })

        return health_status
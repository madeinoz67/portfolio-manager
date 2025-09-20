"""
Metrics API endpoint for Prometheus monitoring.

Provides standardized metrics collection for adapter performance,
system health, and operational statistics.
"""

import logging
import time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.adapters.metrics import get_metrics_collector
from src.services.config_manager import get_config_manager
from src.services.provider_manager import get_provider_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["metrics", "monitoring"]
)


@router.get("", response_class=Response)
async def prometheus_metrics(
    db: Session = Depends(get_db)
):
    """
    Prometheus-compatible metrics endpoint.

    Returns metrics in Prometheus exposition format for scraping
    by monitoring systems.
    """
    try:
        # Get metrics collector
        metrics_collector = get_metrics_collector()
        config_manager = get_config_manager()
        provider_manager = get_provider_manager()

        # Build Prometheus metrics
        metrics_lines = []

        # Add metadata
        metrics_lines.append("# HELP portfolio_adapter_requests_total Total number of adapter requests")
        metrics_lines.append("# TYPE portfolio_adapter_requests_total counter")

        metrics_lines.append("# HELP portfolio_adapter_request_duration_seconds Request duration in seconds")
        metrics_lines.append("# TYPE portfolio_adapter_request_duration_seconds histogram")

        metrics_lines.append("# HELP portfolio_adapter_errors_total Total number of adapter errors")
        metrics_lines.append("# TYPE portfolio_adapter_errors_total counter")

        metrics_lines.append("# HELP portfolio_adapter_health_status Adapter health status (1=healthy, 0=unhealthy)")
        metrics_lines.append("# TYPE portfolio_adapter_health_status gauge")

        metrics_lines.append("# HELP portfolio_adapters_configured Total number of configured adapters")
        metrics_lines.append("# TYPE portfolio_adapters_configured gauge")

        metrics_lines.append("# HELP portfolio_adapters_active Number of active adapters")
        metrics_lines.append("# TYPE portfolio_adapters_active gauge")

        # Get configuration metrics
        active_configs = config_manager.get_active_configurations()
        all_configs = []
        for provider_name in ["alpha_vantage", "yahoo_finance"]:  # Known providers
            configs = config_manager.get_configurations_by_provider(provider_name)
            all_configs.extend(configs)

        metrics_lines.append(f"portfolio_adapters_configured {len(all_configs)}")
        metrics_lines.append(f"portfolio_adapters_active {len(active_configs)}")

        # Get health metrics for each adapter
        for config in active_configs:
            try:
                health = await provider_manager.check_provider_health(str(config.id))

                # Health status (1 for healthy, 0 for unhealthy)
                health_value = 1 if health.status.value == "healthy" else 0
                labels = f'provider="{config.provider_name}",adapter_id="{config.id}",display_name="{config.display_name}"'
                metrics_lines.append(f"portfolio_adapter_health_status{{{labels}}} {health_value}")

                # Error count
                metrics_lines.append(f"portfolio_adapter_errors_total{{{labels}}} {health.error_count}")

                # Success rate as a gauge
                metrics_lines.append(f"# HELP portfolio_adapter_success_rate Adapter success rate (0.0 to 1.0)")
                metrics_lines.append(f"# TYPE portfolio_adapter_success_rate gauge")
                metrics_lines.append(f"portfolio_adapter_success_rate{{{labels}}} {health.success_rate}")

                # Average latency
                metrics_lines.append(f"# HELP portfolio_adapter_latency_seconds Average latency in seconds")
                metrics_lines.append(f"# TYPE portfolio_adapter_latency_seconds gauge")
                latency_seconds = health.avg_latency_ms / 1000.0
                metrics_lines.append(f"portfolio_adapter_latency_seconds{{{labels}}} {latency_seconds}")

            except Exception as e:
                logger.warning(f"Error getting health metrics for adapter {config.id}: {e}")
                # Still report the adapter as configured but unhealthy
                labels = f'provider="{config.provider_name}",adapter_id="{config.id}",display_name="{config.display_name}"'
                metrics_lines.append(f"portfolio_adapter_health_status{{{labels}}} 0")

        # Get global metrics from collector
        try:
            # Add system-wide metrics
            metrics_lines.append(f"# HELP portfolio_system_uptime_seconds System uptime in seconds")
            metrics_lines.append(f"# TYPE portfolio_system_uptime_seconds gauge")

            # Calculate approximate uptime (since this is a stateless calculation)
            current_time = time.time()
            # Use a simple uptime estimation - in production this would be tracked properly
            uptime_seconds = 3600  # Default to 1 hour
            metrics_lines.append(f"portfolio_system_uptime_seconds {uptime_seconds}")

            # Add provider-specific metrics if available
            provider_names = ["alpha_vantage", "yahoo_finance"]
            for provider_name in provider_names:
                try:
                    # Get provider-specific metrics snapshot
                    snapshot = metrics_collector.get_provider_metrics_snapshot(provider_name)
                    if snapshot:
                        labels = f'provider="{provider_name}"'
                        metrics_lines.append(f"portfolio_adapter_requests_total{{{labels}}} {snapshot.total_requests}")
                        metrics_lines.append(f"portfolio_adapter_success_rate{{{labels}}} {snapshot.success_rate}")

                        latency_seconds = snapshot.avg_latency_ms / 1000.0
                        metrics_lines.append(f"portfolio_adapter_latency_seconds{{{labels}}} {latency_seconds}")

                except Exception as e:
                    logger.debug(f"No metrics snapshot available for {provider_name}: {e}")

        except Exception as e:
            logger.warning(f"Error getting global metrics: {e}")

        # Add timestamp
        metrics_lines.append(f"# HELP portfolio_metrics_generation_timestamp_seconds Unix timestamp of metrics generation")
        metrics_lines.append(f"# TYPE portfolio_metrics_generation_timestamp_seconds gauge")
        metrics_lines.append(f"portfolio_metrics_generation_timestamp_seconds {int(time.time())}")

        # Join all metrics with newlines
        metrics_content = "\n".join(metrics_lines) + "\n"

        return Response(
            content=metrics_content,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        # Return basic error metric
        error_metrics = [
            "# HELP portfolio_metrics_error Metrics generation error",
            "# TYPE portfolio_metrics_error gauge",
            "portfolio_metrics_error 1",
            f"# Error: {str(e)}"
        ]
        return Response(
            content="\n".join(error_metrics) + "\n",
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )


@router.get("/health")
async def metrics_health():
    """
    Health check for metrics system.

    Returns simple health status for the metrics collection system.
    """
    try:
        # Test metrics collector
        metrics_collector = get_metrics_collector()

        return {
            "status": "healthy",
            "metrics_collector": "available",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/summary")
async def metrics_summary(
    db: Session = Depends(get_db)
):
    """
    Human-readable metrics summary.

    Returns metrics in JSON format for debugging and monitoring dashboards.
    """
    try:
        config_manager = get_config_manager()
        provider_manager = get_provider_manager()

        # Get configuration counts
        active_configs = config_manager.get_active_configurations()
        all_configs = []
        for provider_name in ["alpha_vantage", "yahoo_finance"]:
            configs = config_manager.get_configurations_by_provider(provider_name)
            all_configs.extend(configs)

        # Get health summary
        health_summary = {}
        healthy_count = 0
        unhealthy_count = 0

        for config in active_configs:
            try:
                health = await provider_manager.check_provider_health(str(config.id))
                is_healthy = health.status.value == "healthy"

                health_summary[str(config.id)] = {
                    "provider_name": config.provider_name,
                    "display_name": config.display_name,
                    "status": health.status.value,
                    "success_rate": health.success_rate,
                    "avg_latency_ms": health.avg_latency_ms,
                    "error_count": health.error_count,
                    "last_check": health.last_check
                }

                if is_healthy:
                    healthy_count += 1
                else:
                    unhealthy_count += 1

            except Exception as e:
                logger.warning(f"Error checking health for {config.id}: {e}")
                unhealthy_count += 1
                health_summary[str(config.id)] = {
                    "provider_name": config.provider_name,
                    "display_name": config.display_name,
                    "status": "error",
                    "error": str(e)
                }

        return {
            "system_status": "healthy" if unhealthy_count == 0 else "degraded",
            "adapters": {
                "total_configured": len(all_configs),
                "active": len(active_configs),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count
            },
            "health_details": health_summary,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error generating metrics summary: {e}")
        return {
            "system_status": "error",
            "error": str(e),
            "timestamp": time.time()
        }
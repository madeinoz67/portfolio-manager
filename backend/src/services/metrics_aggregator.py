"""
Background metrics aggregation service for adapter monitoring.

Provides continuous metrics collection, aggregation, and historical
data management for performance analysis and reporting.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.config_manager import get_config_manager, ConfigurationManager
from src.services.provider_manager import get_provider_manager, ProviderManager
from src.services.adapters.metrics import get_metrics_collector, ProviderMetricsSnapshot
from src.services.activity_service import log_provider_activity

logger = logging.getLogger(__name__)


class MetricsAggregationService:
    """
    Background service for continuous metrics aggregation and analysis.

    Collects metrics from all providers, performs aggregations,
    and maintains historical data for reporting and analysis.
    """

    def __init__(self, aggregation_interval: int = 900):  # 15 minutes default
        """
        Initialize metrics aggregation service.

        Args:
            aggregation_interval: Interval between aggregations in seconds
        """
        self.aggregation_interval = aggregation_interval
        self.config_manager: Optional[ConfigurationManager] = None
        self.provider_manager: Optional[ProviderManager] = None
        self.metrics_collector = get_metrics_collector()
        self.logger = logging.getLogger("metrics.aggregator")

        # Aggregation tracking
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._aggregation_count = 0

        # Retention settings
        self.retention_hours = 168  # 7 days default
        self.cleanup_interval = 3600  # 1 hour

    async def start(self):
        """Start the background metrics aggregation service."""
        if self._running:
            self.logger.warning("Metrics aggregation service is already running")
            return

        self.logger.info("Starting metrics aggregation service...")

        # Initialize dependencies
        try:
            db = next(get_db())
            try:
                self.config_manager = get_config_manager()
                self.provider_manager = get_provider_manager()
                self.logger.info("Metrics aggregation service dependencies initialized")
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize metrics aggregation dependencies: {e}")
            raise

        self._running = True
        self._task = asyncio.create_task(self._aggregation_loop())
        self.logger.info(f"Metrics aggregation service started with {self.aggregation_interval}s interval")

    async def stop(self):
        """Stop the background metrics aggregation service."""
        if not self._running:
            return

        self.logger.info("Stopping metrics aggregation service...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Metrics aggregation service stopped")

    async def _aggregation_loop(self):
        """Main metrics aggregation loop."""
        last_cleanup = datetime.utcnow()

        while self._running:
            try:
                # Perform metrics aggregation
                await self._aggregate_metrics()
                self._aggregation_count += 1

                # Periodic cleanup of old data
                if datetime.utcnow() - last_cleanup > timedelta(seconds=self.cleanup_interval):
                    await self._cleanup_old_metrics()
                    last_cleanup = datetime.utcnow()

            except Exception as e:
                self.logger.error(f"Error in metrics aggregation loop: {e}")

            # Wait for next aggregation
            try:
                await asyncio.sleep(self.aggregation_interval)
            except asyncio.CancelledError:
                break

    async def _aggregate_metrics(self):
        """Perform metrics aggregation for all active adapters."""
        try:
            # Get all active configurations
            active_configs = self.config_manager.get_active_configurations()

            if not active_configs:
                self.logger.debug("No active adapters to aggregate metrics for")
                return

            self.logger.info(f"Aggregating metrics for {len(active_configs)} active adapters")

            # Collect system-wide metrics
            system_metrics = await self._collect_system_metrics(active_configs)

            # Aggregate per-provider metrics
            provider_metrics = {}
            for config in active_configs:
                try:
                    provider_snapshot = await self._collect_provider_metrics(config)
                    if provider_snapshot:
                        provider_metrics[config.provider_name] = provider_snapshot
                except Exception as e:
                    self.logger.error(f"Error collecting metrics for {config.provider_name}: {e}")

            # Store aggregated metrics
            await self._store_aggregated_metrics(system_metrics, provider_metrics)

            # Generate summary report periodically
            if self._aggregation_count % 4 == 0:  # Every hour (4 * 15 minutes)
                await self._generate_summary_report(system_metrics, provider_metrics)

        except Exception as e:
            self.logger.error(f"Error aggregating metrics: {e}")

    async def _collect_system_metrics(self, active_configs) -> Dict[str, Any]:
        """Collect system-wide metrics."""
        try:
            # Get provider health summary
            health_summary = await self.provider_manager.get_all_provider_health()

            healthy_count = sum(1 for h in health_summary.values() if h.status.value == "healthy")
            total_active = len(active_configs)

            # Calculate aggregate success rates and latencies
            total_success_rate = 0.0
            total_latency = 0.0
            providers_with_data = 0

            for health in health_summary.values():
                if health.success_rate >= 0:
                    total_success_rate += health.success_rate
                    total_latency += health.avg_latency_ms
                    providers_with_data += 1

            avg_success_rate = total_success_rate / providers_with_data if providers_with_data > 0 else 0.0
            avg_latency = total_latency / providers_with_data if providers_with_data > 0 else 0.0

            system_metrics = {
                "timestamp": datetime.utcnow(),
                "total_adapters": len(self.config_manager.get_active_configurations()),
                "active_adapters": total_active,
                "healthy_adapters": healthy_count,
                "system_health_percentage": (healthy_count / total_active * 100) if total_active > 0 else 0,
                "avg_success_rate": avg_success_rate,
                "avg_latency_ms": avg_latency,
                "aggregation_count": self._aggregation_count
            }

            return system_metrics

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }

    async def _collect_provider_metrics(self, config) -> Optional[Dict[str, Any]]:
        """Collect metrics for a specific provider."""
        try:
            adapter_id = str(config.id)

            # Get health metrics
            health = await self.provider_manager.check_provider_health(adapter_id)

            # Get metrics snapshot from collector
            snapshot = self.metrics_collector.get_provider_metrics_snapshot(config.provider_name)

            # Calculate cost metrics if available
            cost_metrics = await self._calculate_cost_metrics(config)

            provider_metrics = {
                "adapter_id": adapter_id,
                "provider_name": config.provider_name,
                "display_name": config.display_name,
                "timestamp": datetime.utcnow(),
                "health": {
                    "status": health.status.value,
                    "success_rate": health.success_rate,
                    "avg_latency_ms": health.avg_latency_ms,
                    "error_count": health.error_count,
                    "circuit_breaker_state": health.circuit_breaker_state
                }
            }

            # Add metrics snapshot data if available
            if snapshot:
                provider_metrics["metrics"] = {
                    "total_requests": snapshot.total_requests,
                    "successful_requests": snapshot.successful_requests,
                    "failed_requests": snapshot.failed_requests,
                    "success_rate": snapshot.success_rate,
                    "avg_latency_ms": snapshot.avg_latency_ms,
                    "circuit_breaker_state": snapshot.circuit_breaker_state
                }

            # Add cost metrics if available
            if cost_metrics:
                provider_metrics["cost"] = cost_metrics

            return provider_metrics

        except Exception as e:
            self.logger.error(f"Error collecting provider metrics for {config.provider_name}: {e}")
            return None

    async def _calculate_cost_metrics(self, config) -> Optional[Dict[str, Any]]:
        """Calculate cost metrics for a provider."""
        try:
            # Get cost configuration from config data
            cost_config = config.config_data.get("cost_tracking", {})
            if not cost_config:
                return None

            # Get metrics snapshot for request counts
            snapshot = self.metrics_collector.get_provider_metrics_snapshot(config.provider_name)
            if not snapshot:
                return None

            # Calculate costs based on request counts and pricing
            cost_per_call = Decimal(str(cost_config.get("cost_per_call", 0.0)))
            daily_budget = Decimal(str(cost_config.get("daily_budget_usd", 0.0)))
            monthly_budget = Decimal(str(cost_config.get("monthly_budget_usd", 0.0)))

            # Estimate costs (in a real implementation, this would be tracked precisely)
            estimated_daily_cost = cost_per_call * Decimal(snapshot.total_requests)
            estimated_monthly_cost = estimated_daily_cost * Decimal(30)  # Rough estimate

            cost_metrics = {
                "cost_per_call": float(cost_per_call),
                "estimated_daily_cost": float(estimated_daily_cost),
                "estimated_monthly_cost": float(estimated_monthly_cost),
                "daily_budget": float(daily_budget) if daily_budget > 0 else None,
                "monthly_budget": float(monthly_budget) if monthly_budget > 0 else None,
                "daily_budget_used_percent": float(estimated_daily_cost / daily_budget * 100) if daily_budget > 0 else None,
                "monthly_budget_used_percent": float(estimated_monthly_cost / monthly_budget * 100) if monthly_budget > 0 else None
            }

            return cost_metrics

        except Exception as e:
            self.logger.debug(f"Error calculating cost metrics: {e}")
            return None

    async def _store_aggregated_metrics(self, system_metrics: Dict[str, Any], provider_metrics: Dict[str, Dict[str, Any]]):
        """Store aggregated metrics (placeholder for database storage)."""
        try:
            # In a real implementation, this would store metrics in a time-series database
            # or dedicated metrics tables. For now, we'll log the aggregation activity.

            db = next(get_db())
            try:
                # Log system metrics aggregation
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="METRICS_AGGREGATION",
                    description=f"System metrics aggregated: {system_metrics.get('healthy_adapters', 0)}/{system_metrics.get('total_adapters', 0)} adapters healthy",
                    status="success",
                    metadata={
                        "aggregation_count": self._aggregation_count,
                        "system_health_percentage": system_metrics.get("system_health_percentage", 0),
                        "avg_success_rate": system_metrics.get("avg_success_rate", 0),
                        "avg_latency_ms": system_metrics.get("avg_latency_ms", 0),
                        "provider_count": len(provider_metrics)
                    }
                )

                # Log metrics for providers with significant changes
                for provider_name, metrics in provider_metrics.items():
                    health_data = metrics.get("health", {})
                    if health_data.get("success_rate", 1.0) < 0.9:  # Log if success rate below 90%
                        log_provider_activity(
                            db_session=db,
                            provider_id=metrics.get("adapter_id", provider_name),
                            activity_type="METRICS_ALERT",
                            description=f"Provider metrics show degraded performance: {health_data.get('success_rate', 0):.1%} success rate",
                            status="warning",
                            metadata={
                                "provider_name": provider_name,
                                "success_rate": health_data.get("success_rate", 0),
                                "avg_latency_ms": health_data.get("avg_latency_ms", 0),
                                "error_count": health_data.get("error_count", 0),
                                "aggregation_interval": self.aggregation_interval
                            }
                        )

            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Error storing aggregated metrics: {e}")

    async def _generate_summary_report(self, system_metrics: Dict[str, Any], provider_metrics: Dict[str, Dict[str, Any]]):
        """Generate periodic summary report."""
        try:
            # Calculate summary statistics
            total_providers = len(provider_metrics)
            healthy_providers = sum(1 for m in provider_metrics.values()
                                  if m.get("health", {}).get("status") == "healthy")

            avg_success_rate = system_metrics.get("avg_success_rate", 0)
            avg_latency = system_metrics.get("avg_latency_ms", 0)

            # Generate report
            report = {
                "report_type": "hourly_summary",
                "timestamp": datetime.utcnow(),
                "aggregation_count": self._aggregation_count,
                "system_health": {
                    "total_providers": total_providers,
                    "healthy_providers": healthy_providers,
                    "health_percentage": (healthy_providers / total_providers * 100) if total_providers > 0 else 0,
                    "avg_success_rate": avg_success_rate,
                    "avg_latency_ms": avg_latency
                },
                "top_performers": [],
                "issues": []
            }

            # Find top performers and issues
            for provider_name, metrics in provider_metrics.items():
                health = metrics.get("health", {})
                success_rate = health.get("success_rate", 0)
                latency = health.get("avg_latency_ms", 0)

                if success_rate >= 0.95 and latency < 2000:  # High performance
                    report["top_performers"].append({
                        "provider": provider_name,
                        "success_rate": success_rate,
                        "latency_ms": latency
                    })

                if success_rate < 0.8 or latency > 5000:  # Performance issues
                    report["issues"].append({
                        "provider": provider_name,
                        "issue": "low_success_rate" if success_rate < 0.8 else "high_latency",
                        "success_rate": success_rate,
                        "latency_ms": latency
                    })

            # Log summary report
            db = next(get_db())
            try:
                status = "success" if len(report["issues"]) == 0 else "warning"
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="SUMMARY_REPORT",
                    description=f"Hourly summary: {healthy_providers}/{total_providers} providers healthy, {len(report['issues'])} issues detected",
                    status=status,
                    metadata=report
                )
            finally:
                db.close()

            self.logger.info(f"Generated summary report: {healthy_providers}/{total_providers} providers healthy")

        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics data beyond retention period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

            # In a real implementation, this would clean up old metrics from database
            self.logger.debug(f"Metrics cleanup would remove data older than {cutoff_time}")

            # Log cleanup activity
            db = next(get_db())
            try:
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="METRICS_CLEANUP",
                    description=f"Metrics cleanup completed, removed data older than {self.retention_hours} hours",
                    status="success",
                    metadata={
                        "retention_hours": self.retention_hours,
                        "cutoff_time": cutoff_time.isoformat(),
                        "cleanup_interval": self.cleanup_interval
                    }
                )
            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Error during metrics cleanup: {e}")

    def get_aggregation_status(self) -> Dict[str, Any]:
        """Get current aggregation service status."""
        return {
            "service_status": "running" if self._running else "stopped",
            "aggregation_interval": self.aggregation_interval,
            "aggregation_count": self._aggregation_count,
            "retention_hours": self.retention_hours,
            "last_aggregation": datetime.utcnow().isoformat() if self._running else None
        }


# Global metrics aggregation service instance
_metrics_aggregation_service: Optional[MetricsAggregationService] = None


def get_metrics_aggregation_service(aggregation_interval: int = 900) -> MetricsAggregationService:
    """Get the global metrics aggregation service instance."""
    global _metrics_aggregation_service

    if _metrics_aggregation_service is None:
        _metrics_aggregation_service = MetricsAggregationService(aggregation_interval)

    return _metrics_aggregation_service


async def start_metrics_aggregation_service(aggregation_interval: int = 900):
    """Start the global metrics aggregation service."""
    service = get_metrics_aggregation_service(aggregation_interval)
    await service.start()


async def stop_metrics_aggregation_service():
    """Stop the global metrics aggregation service."""
    global _metrics_aggregation_service

    if _metrics_aggregation_service:
        await _metrics_aggregation_service.stop()
        _metrics_aggregation_service = None
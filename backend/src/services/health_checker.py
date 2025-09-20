"""
Background health check service for adapter monitoring.

Provides continuous health monitoring of all configured adapters
with automatic alerting and recovery detection.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.config_manager import get_config_manager, ConfigurationManager
from src.services.provider_manager import get_provider_manager, ProviderManager, ProviderStatus, ProviderHealth
from src.services.activity_service import log_provider_activity

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Background service for continuous adapter health monitoring.

    Performs periodic health checks, tracks status changes,
    and provides alerting for critical issues.
    """

    def __init__(self, check_interval: int = 300):  # 5 minutes default
        """
        Initialize health check service.

        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self.config_manager: Optional[ConfigurationManager] = None
        self.provider_manager: Optional[ProviderManager] = None
        self.logger = logging.getLogger("health.checker")

        # Health tracking
        self._health_history: Dict[str, List[ProviderHealth]] = {}
        self._last_status: Dict[str, ProviderStatus] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Alert thresholds
        self.failure_threshold = 3  # Consecutive failures before alert
        self.recovery_threshold = 2  # Consecutive successes for recovery

    async def start(self):
        """Start the background health check service."""
        if self._running:
            self.logger.warning("Health check service is already running")
            return

        self.logger.info("Starting health check service...")

        # Initialize dependencies
        try:
            # Use a database session to initialize managers
            db = next(get_db())
            try:
                self.config_manager = get_config_manager()
                self.provider_manager = get_provider_manager()
                self.logger.info("Health check service dependencies initialized")
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize health check dependencies: {e}")
            raise

        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        self.logger.info(f"Health check service started with {self.check_interval}s interval")

    async def stop(self):
        """Stop the background health check service."""
        if not self._running:
            return

        self.logger.info("Stopping health check service...")
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Health check service stopped")

    async def _health_check_loop(self):
        """Main health check loop."""
        while self._running:
            try:
                await self._perform_health_checks()
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")

            # Wait for next check
            try:
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break

    async def _perform_health_checks(self):
        """Perform health checks on all active adapters."""
        try:
            # Get all active configurations
            active_configs = self.config_manager.get_active_configurations()

            if not active_configs:
                self.logger.debug("No active adapters to check")
                return

            self.logger.info(f"Performing health checks on {len(active_configs)} active adapters")

            # Check each adapter
            for config in active_configs:
                try:
                    await self._check_adapter_health(config)
                except Exception as e:
                    self.logger.error(f"Error checking health for adapter {config.id}: {e}")

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")

    async def _check_adapter_health(self, config):
        """Check health of a specific adapter configuration."""
        adapter_id = str(config.id)

        try:
            # Perform health check
            health = await self.provider_manager.check_provider_health(adapter_id)

            # Store health history
            if adapter_id not in self._health_history:
                self._health_history[adapter_id] = []

            self._health_history[adapter_id].append(health)

            # Keep only recent history (last 10 checks)
            if len(self._health_history[adapter_id]) > 10:
                self._health_history[adapter_id] = self._health_history[adapter_id][-10:]

            # Check for status changes
            previous_status = self._last_status.get(adapter_id)
            current_status = health.status

            if previous_status != current_status:
                await self._handle_status_change(config, previous_status, current_status, health)

            self._last_status[adapter_id] = current_status

            # Check for alert conditions
            await self._check_alert_conditions(config, health)

        except Exception as e:
            self.logger.error(f"Health check failed for adapter {adapter_id}: {e}")

            # Log health check failure as activity
            try:
                db = next(get_db())
                try:
                    log_provider_activity(
                        db_session=db,
                        provider_id=adapter_id,
                        activity_type="HEALTH_CHECK_ERROR",
                        description=f"Health check failed: {str(e)}",
                        status="error",
                        metadata={
                            "error": str(e),
                            "provider_name": config.provider_name,
                            "display_name": config.display_name
                        }
                    )
                finally:
                    db.close()
            except Exception as log_error:
                self.logger.error(f"Failed to log health check error: {log_error}")

    async def _handle_status_change(self, config, previous_status, current_status, health):
        """Handle adapter status changes."""
        adapter_id = str(config.id)

        self.logger.info(
            f"Adapter {config.display_name} status changed: "
            f"{previous_status.value if previous_status else 'unknown'} -> {current_status.value}"
        )

        # Log status change activity
        try:
            db = next(get_db())
            try:
                activity_type = "STATUS_CHANGE"
                status = "success" if current_status == ProviderStatus.HEALTHY else "warning"

                # Special handling for critical status changes
                if current_status == ProviderStatus.UNHEALTHY:
                    activity_type = "PROVIDER_FAILURE"
                    status = "error"
                elif current_status == ProviderStatus.HEALTHY and previous_status in [ProviderStatus.UNHEALTHY, ProviderStatus.CIRCUIT_OPEN]:
                    activity_type = "PROVIDER_RECOVERY"
                    status = "success"

                log_provider_activity(
                    db_session=db,
                    provider_id=adapter_id,
                    activity_type=activity_type,
                    description=f"Provider status changed from {previous_status.value if previous_status else 'unknown'} to {current_status.value}",
                    status=status,
                    metadata={
                        "previous_status": previous_status.value if previous_status else None,
                        "current_status": current_status.value,
                        "success_rate": health.success_rate,
                        "avg_latency_ms": health.avg_latency_ms,
                        "error_count": health.error_count,
                        "provider_name": config.provider_name,
                        "display_name": config.display_name
                    }
                )
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to log status change activity: {e}")

    async def _check_alert_conditions(self, config, health):
        """Check for conditions that require alerts."""
        adapter_id = str(config.id)

        # Get recent health history
        recent_health = self._health_history.get(adapter_id, [])
        if len(recent_health) < 2:
            return  # Not enough history for alerting

        # Check for consecutive failures
        recent_statuses = [h.status for h in recent_health[-self.failure_threshold:]]
        if (len(recent_statuses) >= self.failure_threshold and
            all(status in [ProviderStatus.UNHEALTHY, ProviderStatus.CIRCUIT_OPEN] for status in recent_statuses)):

            await self._trigger_failure_alert(config, health, recent_health)

        # Check for recovery
        if (len(recent_statuses) >= self.recovery_threshold and
            all(status == ProviderStatus.HEALTHY for status in recent_statuses[-self.recovery_threshold:])):

            # Check if we were previously unhealthy
            if len(recent_statuses) > self.recovery_threshold:
                earlier_status = recent_statuses[-(self.recovery_threshold + 1)]
                if earlier_status in [ProviderStatus.UNHEALTHY, ProviderStatus.CIRCUIT_OPEN]:
                    await self._trigger_recovery_alert(config, health)

        # Check for performance degradation
        if health.status == ProviderStatus.HEALTHY:
            if health.success_rate < 0.8:  # Less than 80% success rate
                await self._trigger_performance_alert(config, health, "low_success_rate")
            elif health.avg_latency_ms > 5000:  # More than 5 seconds average latency
                await self._trigger_performance_alert(config, health, "high_latency")

    async def _trigger_failure_alert(self, config, health, recent_health):
        """Trigger alert for consecutive failures."""
        self.logger.warning(
            f"ALERT: Adapter {config.display_name} has failed {self.failure_threshold} consecutive health checks"
        )

        try:
            db = next(get_db())
            try:
                log_provider_activity(
                    db_session=db,
                    provider_id=str(config.id),
                    activity_type="FAILURE_ALERT",
                    description=f"Adapter failed {self.failure_threshold} consecutive health checks",
                    status="critical",
                    metadata={
                        "alert_type": "consecutive_failures",
                        "failure_count": self.failure_threshold,
                        "current_status": health.status.value,
                        "success_rate": health.success_rate,
                        "error_count": health.error_count,
                        "provider_name": config.provider_name,
                        "display_name": config.display_name,
                        "recent_checks": len(recent_health)
                    }
                )
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to log failure alert: {e}")

    async def _trigger_recovery_alert(self, config, health):
        """Trigger alert for adapter recovery."""
        self.logger.info(f"RECOVERY: Adapter {config.display_name} has recovered")

        try:
            db = next(get_db())
            try:
                log_provider_activity(
                    db_session=db,
                    provider_id=str(config.id),
                    activity_type="RECOVERY_ALERT",
                    description=f"Adapter has recovered after {self.recovery_threshold} consecutive successful checks",
                    status="success",
                    metadata={
                        "alert_type": "recovery",
                        "recovery_count": self.recovery_threshold,
                        "current_status": health.status.value,
                        "success_rate": health.success_rate,
                        "avg_latency_ms": health.avg_latency_ms,
                        "provider_name": config.provider_name,
                        "display_name": config.display_name
                    }
                )
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to log recovery alert: {e}")

    async def _trigger_performance_alert(self, config, health, alert_reason):
        """Trigger alert for performance issues."""
        reason_messages = {
            "low_success_rate": f"Success rate dropped to {health.success_rate:.1%}",
            "high_latency": f"Average latency increased to {health.avg_latency_ms:.0f}ms"
        }

        message = reason_messages.get(alert_reason, f"Performance issue: {alert_reason}")
        self.logger.warning(f"PERFORMANCE: Adapter {config.display_name} - {message}")

        try:
            db = next(get_db())
            try:
                log_provider_activity(
                    db_session=db,
                    provider_id=str(config.id),
                    activity_type="PERFORMANCE_ALERT",
                    description=f"Performance degradation detected: {message}",
                    status="warning",
                    metadata={
                        "alert_type": "performance",
                        "alert_reason": alert_reason,
                        "success_rate": health.success_rate,
                        "avg_latency_ms": health.avg_latency_ms,
                        "error_count": health.error_count,
                        "provider_name": config.provider_name,
                        "display_name": config.display_name
                    }
                )
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"Failed to log performance alert: {e}")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary for all monitored adapters."""
        summary = {
            "service_status": "running" if self._running else "stopped",
            "check_interval": self.check_interval,
            "monitored_adapters": len(self._health_history),
            "last_check_time": datetime.utcnow().isoformat(),
            "adapters": {}
        }

        for adapter_id, health_list in self._health_history.items():
            if health_list:
                latest_health = health_list[-1]
                summary["adapters"][adapter_id] = {
                    "status": latest_health.status.value,
                    "success_rate": latest_health.success_rate,
                    "avg_latency_ms": latest_health.avg_latency_ms,
                    "error_count": latest_health.error_count,
                    "last_check": latest_health.last_check,
                    "check_count": len(health_list)
                }

        return summary


# Global health check service instance
_health_check_service: Optional[HealthCheckService] = None


def get_health_check_service(check_interval: int = 300) -> HealthCheckService:
    """Get the global health check service instance."""
    global _health_check_service

    if _health_check_service is None:
        _health_check_service = HealthCheckService(check_interval)

    return _health_check_service


async def start_health_check_service(check_interval: int = 300):
    """Start the global health check service."""
    service = get_health_check_service(check_interval)
    await service.start()


async def stop_health_check_service():
    """Stop the global health check service."""
    global _health_check_service

    if _health_check_service:
        await _health_check_service.stop()
        _health_check_service = None
"""
Market data scheduler service for managing scheduled data fetching operations.

Provides centralized control over scheduler state and configuration.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.utils.datetime_utils import utc_now
from src.models.scheduler_execution import SchedulerExecution

logger = get_logger(__name__)


class SchedulerState(str, Enum):
    """Enumeration of scheduler states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class SchedulerConfiguration:
    """Configuration for the market data scheduler."""

    def __init__(
        self,
        interval_minutes: int = 15,
        max_concurrent_jobs: int = 5,
        retry_attempts: int = 3,
        enabled_providers: Optional[List[str]] = None,
        bulk_mode: bool = True,
        timeout_seconds: int = 300
    ):
        self.interval_minutes = interval_minutes
        self.max_concurrent_jobs = max_concurrent_jobs
        self.retry_attempts = retry_attempts
        self.enabled_providers = enabled_providers or []
        self.bulk_mode = bulk_mode
        self.timeout_seconds = timeout_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "interval_minutes": self.interval_minutes,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "retry_attempts": self.retry_attempts,
            "enabled_providers": self.enabled_providers,
            "bulk_mode": self.bulk_mode,
            "timeout_seconds": self.timeout_seconds
        }

    def update_from_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration from dictionary and return changes."""
        changes = {}

        for key, new_value in config_dict.items():
            if hasattr(self, key):
                old_value = getattr(self, key)
                if old_value != new_value:
                    changes[key] = {"old": old_value, "new": new_value}
                    setattr(self, key, new_value)

        return changes


class MarketDataSchedulerService:
    """Service for managing market data scheduler operations."""

    def __init__(self, db: Session, auto_start: bool = True):
        self.db = db
        self._state = SchedulerState.STOPPED
        self._config = SchedulerConfiguration()
        self._last_run = None
        self._next_run = None
        self._pause_until = None
        self._error_message = None

        # Execution tracking metrics
        self._total_executions = 0
        self._successful_executions = 0
        self._failed_executions = 0
        self._total_symbols_processed = 0
        self._last_execution_symbols = 0
        self._current_execution = None  # Track current execution in progress

        # Load execution history from database on startup
        self._load_execution_history()

        # Auto-start the scheduler for production use
        if auto_start:
            self._auto_start()

    @property
    def state(self) -> SchedulerState:
        """Get current scheduler state."""
        # Check if pause period has expired
        if self._state == SchedulerState.PAUSED and self._pause_until:
            if utc_now() >= self._pause_until:
                self._state = SchedulerState.RUNNING
                self._pause_until = None

        return self._state

    @property
    def configuration(self) -> SchedulerConfiguration:
        """Get current scheduler configuration."""
        return self._config

    def get_last_run(self) -> Optional[datetime]:
        """Get the most recent successful execution time from database."""
        try:
            last_execution = (
                self.db.query(SchedulerExecution)
                .filter(SchedulerExecution.status == "success")
                .order_by(SchedulerExecution.completed_at.desc())
                .first()
            )
            return last_execution.completed_at if last_execution else None
        except Exception as e:
            logger.error(f"Failed to get last run from database: {e}")
            return self._last_run

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive scheduler status with database-calculated metrics."""
        # Get metrics from database
        all_executions = self.db.query(SchedulerExecution).all()
        successful_runs = sum(1 for ex in all_executions if ex.status == "success")
        failed_runs = sum(1 for ex in all_executions if ex.status == "failed")
        total_symbols_processed = sum(ex.symbols_processed or 0 for ex in all_executions)

        # Calculate success rate
        total_runs = len(all_executions)
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0.0

        # Get recent activity (last 24 hours)
        recent_cutoff = utc_now() - timedelta(hours=24)
        # Convert to naive datetime for comparison with database datetime
        recent_cutoff_naive = recent_cutoff.replace(tzinfo=None)
        recent_executions = [ex for ex in all_executions if ex.started_at >= recent_cutoff_naive]
        recent_symbols = sum(ex.symbols_processed or 0 for ex in recent_executions)
        recent_success_count = sum(1 for ex in recent_executions if ex.status == "success")
        recent_success_rate = (recent_success_count / len(recent_executions) * 100) if recent_executions else 0.0

        return {
            "state": self.state.value,
            "last_run": self.get_last_run(),
            "next_run": self._next_run,
            "pause_until": self._pause_until,
            "error_message": self._error_message,
            "configuration": self._config.to_dict(),
            "uptime_seconds": self._calculate_uptime_seconds(),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": success_rate,
            "total_symbols_processed": total_symbols_processed,
            "recent_activity": {
                "total_symbols_processed": recent_symbols,
                "success_rate": recent_success_rate
            }
        }

    @property
    def status_info(self) -> Dict[str, Any]:
        """Get comprehensive scheduler status information."""
        # Calculate success rate
        success_rate = 0.0
        if self._total_executions > 0:
            success_rate = (self._successful_executions / self._total_executions) * 100

        return {
            "state": self.state.value,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "pause_until": self._pause_until.isoformat() if self._pause_until else None,
            "error_message": self._error_message,
            "configuration": self._config.to_dict(),
            "uptime_seconds": self._calculate_uptime_seconds(),
            # Execution metrics for admin UI
            "total_executions": self._total_executions,
            "successful_executions": self._successful_executions,
            "failed_executions": self._failed_executions,
            "success_rate_percent": success_rate,
            "total_symbols_processed": self._total_symbols_processed,
            "last_execution_symbols": self._last_execution_symbols
        }

    def _auto_start(self) -> None:
        """Automatically start the scheduler with default configuration."""
        try:
            self._state = SchedulerState.RUNNING
            self._error_message = None
            self._calculate_next_run()
            logger.info("Market data scheduler auto-started with 15min intervals")
        except Exception as e:
            logger.error(f"Failed to auto-start scheduler: {e}")
            self._state = SchedulerState.ERROR
            self._error_message = str(e)

    def start(self, config_override: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start the scheduler.

        Args:
            config_override: Optional configuration overrides

        Returns:
            True if started successfully, False otherwise
        """
        try:
            if config_override:
                self._config.update_from_dict(config_override)

            self._state = SchedulerState.RUNNING
            self._error_message = None
            self._calculate_next_run()

            logger.info(f"Market data scheduler started with {self._config.interval_minutes}min intervals")
            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self._state = SchedulerState.ERROR
            self._error_message = str(e)
            return False

    def stop(self, reason: Optional[str] = None) -> bool:
        """
        Stop the scheduler.

        Args:
            reason: Optional reason for stopping

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            self._state = SchedulerState.STOPPED
            self._next_run = None
            self._pause_until = None
            self._error_message = None

            logger.info(f"Market data scheduler stopped. Reason: {reason or 'manual_stop'}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            self._error_message = str(e)
            return False

    def pause(self, duration_minutes: Optional[int] = None) -> bool:
        """
        Pause the scheduler.

        Args:
            duration_minutes: Optional duration to pause (None = indefinite)

        Returns:
            True if paused successfully, False otherwise
        """
        try:
            if self._state != SchedulerState.RUNNING:
                logger.warning(f"Cannot pause scheduler in state: {self._state}")
                return False

            self._state = SchedulerState.PAUSED

            if duration_minutes:
                self._pause_until = utc_now() + timedelta(minutes=duration_minutes)
                logger.info(f"Market data scheduler paused for {duration_minutes} minutes")
            else:
                self._pause_until = None
                logger.info("Market data scheduler paused indefinitely")

            return True

        except Exception as e:
            logger.error(f"Failed to pause scheduler: {e}")
            self._error_message = str(e)
            return False

    def resume(self) -> bool:
        """
        Resume the scheduler from paused state.

        Returns:
            True if resumed successfully, False otherwise
        """
        try:
            if self._state != SchedulerState.PAUSED:
                logger.warning(f"Cannot resume scheduler in state: {self._state}")
                return False

            self._state = SchedulerState.RUNNING
            self._pause_until = None
            self._calculate_next_run()

            logger.info("Market data scheduler resumed")
            return True

        except Exception as e:
            logger.error(f"Failed to resume scheduler: {e}")
            self._error_message = str(e)
            return False

    def update_configuration(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update scheduler configuration.

        Args:
            config_updates: Dictionary of configuration updates

        Returns:
            Dictionary of actual changes made
        """
        try:
            changes = self._config.update_from_dict(config_updates)

            # Recalculate next run if interval changed and scheduler is running
            if "interval_minutes" in changes and self._state == SchedulerState.RUNNING:
                self._calculate_next_run()

            logger.info(f"Scheduler configuration updated: {changes}")
            return changes

        except Exception as e:
            logger.error(f"Failed to update scheduler configuration: {e}")
            self._error_message = str(e)
            return {}

    def _calculate_next_run(self):
        """Calculate the next scheduled run time."""
        if self._state == SchedulerState.RUNNING:
            self._next_run = utc_now().replace(tzinfo=None) + timedelta(minutes=self._config.interval_minutes)
        else:
            self._next_run = None

    def _calculate_uptime_seconds(self) -> Optional[int]:
        """Calculate scheduler uptime in seconds."""
        if self._state == SchedulerState.RUNNING and self._last_run:
            # Convert timezone-aware utc_now to naive for comparison with database datetime
            now_naive = utc_now().replace(tzinfo=None)
            return int((now_naive - self._last_run).total_seconds())
        return None

    def _load_execution_history(self) -> None:
        """Load execution history from database on startup."""
        try:
            # Get all executions to calculate metrics
            all_executions = self.db.query(SchedulerExecution).all()

            # Update in-memory metrics from database
            self._total_executions = len(all_executions)
            self._successful_executions = sum(1 for ex in all_executions if ex.status == "success")
            self._failed_executions = sum(1 for ex in all_executions if ex.status == "failed")
            self._total_symbols_processed = sum(ex.symbols_processed or 0 for ex in all_executions)

            # Get most recent execution for last run
            last_execution = (
                self.db.query(SchedulerExecution)
                .filter(SchedulerExecution.status == "success")
                .order_by(SchedulerExecution.completed_at.desc())
                .first()
            )

            if last_execution:
                self._last_run = last_execution.completed_at
                self._last_execution_symbols = last_execution.symbols_processed or 0

            logger.info(f"Loaded execution history: {self._total_executions} total, {self._successful_executions} successful")

        except Exception as e:
            logger.error(f"Failed to load execution history: {e}")
            # Keep default values if database load fails

    def record_execution_start(self) -> None:
        """Record that a scheduler execution has started."""
        if self._state == SchedulerState.RUNNING:
            # Create database record for execution start (using naive datetime for database)
            start_time = utc_now().replace(tzinfo=None)
            self._current_execution = SchedulerExecution(
                started_at=start_time,
                status="running",
                symbols_processed=0,
                successful_fetches=0,
                failed_fetches=0
            )
            self.db.add(self._current_execution)
            self.db.commit()
            logger.debug("Scheduler execution started")

    def record_execution_success(self, symbols_processed: int = 0, response_time_ms: Optional[int] = None) -> None:
        """
        Record a successful scheduler execution.

        Args:
            symbols_processed: Number of symbols successfully processed
            response_time_ms: Response time in milliseconds
        """
        if self._state == SchedulerState.RUNNING:
            completion_time = utc_now().replace(tzinfo=None)  # Store naive datetime
            self._last_run = completion_time
            self._calculate_next_run()

            # Update current execution record in database
            if self._current_execution:
                self._current_execution.completed_at = completion_time
                self._current_execution.status = "success"
                self._current_execution.symbols_processed = symbols_processed
                self._current_execution.successful_fetches = symbols_processed  # Assume all successful for now
                self._current_execution.failed_fetches = 0
                if response_time_ms:
                    self._current_execution.execution_time_ms = response_time_ms

                self.db.commit()
                self._current_execution = None

            # Update execution metrics
            self._total_executions += 1
            self._successful_executions += 1
            self._total_symbols_processed += symbols_processed
            self._last_execution_symbols = symbols_processed
            self._error_message = None  # Clear any previous error

            logger.info(f"Scheduler execution completed successfully: {symbols_processed} symbols processed")

    def record_execution_failure(self, error: str) -> None:
        """
        Record a failed scheduler execution.

        Args:
            error: Error message describing the failure
        """
        # Update current execution record in database
        if self._current_execution:
            self._current_execution.completed_at = utc_now().replace(tzinfo=None)  # Store naive datetime
            self._current_execution.status = "failed"
            self._current_execution.error_message = error
            self.db.commit()
            self._current_execution = None

        # Update execution metrics
        self._total_executions += 1
        self._failed_executions += 1
        self._error_message = error

        logger.error(f"Scheduler execution failed: {error}")

    def simulate_run(self) -> Dict[str, Any]:
        """
        Simulate a scheduler run for testing purposes.

        Returns:
            Dictionary with run results
        """
        if self._state != SchedulerState.RUNNING:
            return {"error": f"Scheduler not running (state: {self._state})"}

        self._last_run = utc_now()
        self._calculate_next_run()

        return {
            "status": "completed",
            "run_time": self._last_run.isoformat(),
            "next_run": self._next_run.isoformat(),
            "providers_checked": len(self._config.enabled_providers),
            "symbols_updated": 0  # Would be actual count in real implementation
        }


# Global scheduler service instance
_scheduler_service_instance = None


def get_scheduler_service(db: Session) -> MarketDataSchedulerService:
    """Get or create scheduler service instance."""
    global _scheduler_service_instance

    if _scheduler_service_instance is None:
        _scheduler_service_instance = MarketDataSchedulerService(db)

    return _scheduler_service_instance


def reset_scheduler_service():
    """Reset scheduler service instance (for testing)."""
    global _scheduler_service_instance
    _scheduler_service_instance = None
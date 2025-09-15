"""
Portfolio Update Queue Service with Update Storm Protection.

Implements intelligent batching, debouncing, and rate limiting to prevent
update storms when many stock prices change simultaneously.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from src.core.logging import LoggerMixin


@dataclass
class UpdateRequest:
    """Represents a portfolio update request."""
    portfolio_id: str
    symbols: Set[str]
    timestamp: float
    priority: int = 1  # Higher = more important


class PortfolioUpdateQueue(LoggerMixin):
    """
    Manages portfolio update requests with storm protection.

    Features:
    - Debouncing: Delays updates to batch multiple symbol changes
    - Coalescing: Merges multiple requests for same portfolio
    - Rate limiting: Prevents excessive updates per portfolio
    - Priority queuing: Important updates (like manual refreshes) get priority
    """

    def __init__(self, debounce_seconds: float = 2.0, max_updates_per_minute: int = 20):
        """
        Initialize the update queue.

        Args:
            debounce_seconds: How long to wait for more updates before processing
            max_updates_per_minute: Maximum updates per portfolio per minute
        """
        self.debounce_seconds = debounce_seconds
        self.max_updates_per_minute = max_updates_per_minute

        # Queue management
        self._pending_updates: Dict[str, UpdateRequest] = {}  # portfolio_id -> latest request
        self._update_lock = Lock()

        # Rate limiting tracking
        self._rate_limit_windows: Dict[str, deque] = defaultdict(deque)  # portfolio_id -> timestamps

        # Background processing
        self._processing_task: Optional[asyncio.Task] = None
        self._shutdown = False

        self.log_info("Portfolio Update Queue initialized", extra={
            "debounce_seconds": debounce_seconds,
            "max_updates_per_minute": max_updates_per_minute
        })

    async def start_processing(self):
        """Start the background processing task."""
        if self._processing_task is None or self._processing_task.done():
            self._shutdown = False
            self._processing_task = asyncio.create_task(self._process_queue())
            self.log_info("Portfolio update queue processing started")

    async def stop_processing(self):
        """Stop the background processing task."""
        self._shutdown = True
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        self.log_info("Portfolio update queue processing stopped")

    def queue_portfolio_update(self, portfolio_id: str, symbols: List[str], priority: int = 1) -> bool:
        """
        Queue a portfolio update request.

        Args:
            portfolio_id: ID of portfolio to update
            symbols: List of symbols that changed
            priority: Update priority (higher = more important)

        Returns:
            True if queued, False if rate limited
        """
        try:
            # Check rate limiting
            if not self._check_rate_limit(portfolio_id):
                self.log_warning(f"Rate limit exceeded for portfolio {portfolio_id}, skipping update")
                return False

            current_time = time.time()
            symbol_set = set(symbols)

            with self._update_lock:
                existing_request = self._pending_updates.get(portfolio_id)

                if existing_request:
                    # Coalesce: Merge with existing request
                    existing_request.symbols.update(symbol_set)
                    existing_request.timestamp = current_time  # Reset debounce timer
                    existing_request.priority = max(existing_request.priority, priority)

                    self.log_debug(f"Coalesced update for portfolio {portfolio_id}", extra={
                        "total_symbols": len(existing_request.symbols),
                        "new_symbols": list(symbol_set)
                    })
                else:
                    # New request
                    self._pending_updates[portfolio_id] = UpdateRequest(
                        portfolio_id=portfolio_id,
                        symbols=symbol_set,
                        timestamp=current_time,
                        priority=priority
                    )

                    self.log_debug(f"Queued new update for portfolio {portfolio_id}", extra={
                        "symbols": symbols,
                        "priority": priority
                    })

            return True

        except Exception as e:
            self.log_error(f"Error queuing portfolio update for {portfolio_id}", error=str(e))
            return False

    def _check_rate_limit(self, portfolio_id: str) -> bool:
        """Check if portfolio is within rate limits."""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Clean old timestamps
        timestamps = self._rate_limit_windows[portfolio_id]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        # Check if under limit
        return len(timestamps) < self.max_updates_per_minute

    def _record_update(self, portfolio_id: str):
        """Record that an update was processed for rate limiting."""
        current_time = time.time()
        self._rate_limit_windows[portfolio_id].append(current_time)

    async def _process_queue(self):
        """Background task that processes the update queue."""
        self.log_info("Portfolio update queue processor started")

        try:
            while not self._shutdown:
                await self._process_batch()
                await asyncio.sleep(0.5)  # Check queue every 500ms

        except asyncio.CancelledError:
            self.log_info("Portfolio update queue processor cancelled")
            raise
        except Exception as e:
            self.log_error("Error in portfolio update queue processor", error=str(e))

    async def _process_batch(self):
        """Process a batch of ready updates."""
        ready_updates = []
        current_time = time.time()

        # Find updates that are ready to process (past debounce time)
        with self._update_lock:
            ready_portfolio_ids = []

            for portfolio_id, request in self._pending_updates.items():
                time_since_update = current_time - request.timestamp

                if time_since_update >= self.debounce_seconds:
                    ready_updates.append(request)
                    ready_portfolio_ids.append(portfolio_id)

            # Remove processed requests from queue
            for portfolio_id in ready_portfolio_ids:
                del self._pending_updates[portfolio_id]

        if not ready_updates:
            return

        # Sort by priority (highest first)
        ready_updates.sort(key=lambda x: x.priority, reverse=True)

        self.log_info(f"Processing batch of {len(ready_updates)} portfolio updates")

        # Process each update
        for request in ready_updates:
            try:
                await self._execute_portfolio_update(request)
                self._record_update(request.portfolio_id)

            except Exception as e:
                self.log_error(f"Error executing portfolio update for {request.portfolio_id}", error=str(e))

    async def _execute_portfolio_update(self, request: UpdateRequest):
        """Execute the actual portfolio update."""
        from src.services.real_time_portfolio_service import RealTimePortfolioService
        from src.database import SessionLocal

        try:
            # Use a new database session for this update
            db = SessionLocal()
            portfolio_service = RealTimePortfolioService(db)

            # Update the portfolio with all changed symbols
            updated_portfolios = portfolio_service.bulk_update_portfolios_for_symbols(
                list(request.symbols)
            )

            if updated_portfolios:
                self.log_info(f"Executed portfolio update for {request.portfolio_id}", extra={
                    "symbols": list(request.symbols),
                    "symbol_count": len(request.symbols),
                    "priority": request.priority
                })
            else:
                self.log_warning(f"Portfolio update found no portfolios for {request.portfolio_id}")

        finally:
            if 'db' in locals():
                db.close()

    def get_queue_stats(self) -> Dict:
        """Get current queue statistics for monitoring."""
        with self._update_lock:
            pending_count = len(self._pending_updates)
            portfolio_symbols = {
                pid: len(req.symbols)
                for pid, req in self._pending_updates.items()
            }

        return {
            "pending_updates": pending_count,
            "portfolio_symbol_counts": portfolio_symbols,
            "rate_limit_windows": {
                pid: len(timestamps)
                for pid, timestamps in self._rate_limit_windows.items()
            },
            "is_processing": not (self._processing_task is None or self._processing_task.done()),
            "debounce_seconds": self.debounce_seconds,
            "max_updates_per_minute": self.max_updates_per_minute
        }


# Global instance for the application
_portfolio_queue: Optional[PortfolioUpdateQueue] = None


def get_portfolio_update_queue() -> PortfolioUpdateQueue:
    """Get the global portfolio update queue instance."""
    global _portfolio_queue
    if _portfolio_queue is None:
        _portfolio_queue = PortfolioUpdateQueue()
    return _portfolio_queue


async def initialize_portfolio_queue():
    """Initialize the global portfolio update queue."""
    queue = get_portfolio_update_queue()
    await queue.start_processing()


async def shutdown_portfolio_queue():
    """Shutdown the global portfolio update queue."""
    global _portfolio_queue
    if _portfolio_queue is not None:
        await _portfolio_queue.stop_processing()
"""
Mixins for enhanced adapter functionality.

Provides reusable mixins for common adapter patterns including
circuit breaker, retry logic, rate limiting, and metrics collection.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Union
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from .base_adapter import AdapterResponse, AdapterError, RateLimitError, ProviderTimeoutError

logger = logging.getLogger(__name__)


class ResilientProviderMixin:
    """
    Mixin providing circuit breaker and retry functionality for adapters.

    Implements the circuit breaker pattern to prevent cascading failures
    and provides configurable retry logic with exponential backoff.
    """

    def __init__(self, *args, **kwargs):
        """Initialize resilience components."""
        super().__init__(*args, **kwargs)

        # Circuit breaker configuration
        self._circuit_breaker = CircuitBreaker(
            fail_max=self.config.get("circuit_breaker_fail_max", 5),
            recovery_timeout=self.config.get("circuit_breaker_recovery_timeout", 60),
            expected_exception=AdapterError
        )

        # Retry configuration
        self._retry_attempts = self.config.get("retry_attempts", 3)
        self._retry_wait_min = self.config.get("retry_wait_min", 1)
        self._retry_wait_max = self.config.get("retry_wait_max", 10)

        # Rate limiting
        self._rate_limit_per_minute = self.config.get("rate_limit_per_minute", 60)
        self._request_times = []

        self.logger = logging.getLogger(f"adapter.{self.provider_name}.resilient")

    def _create_retry_decorator(self, exclude_rate_limit: bool = True):
        """Create a retry decorator with configured parameters."""
        retry_exceptions = [ProviderTimeoutError, ConnectionError]
        if not exclude_rate_limit:
            retry_exceptions.append(RateLimitError)

        return retry(
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self._retry_wait_min,
                max=self._retry_wait_max
            ),
            retry=retry_if_exception_type(tuple(retry_exceptions)),
            reraise=True
        )

    async def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if request can proceed, False if rate limited
        """
        now = time.time()
        minute_ago = now - 60

        # Remove old requests
        self._request_times = [t for t in self._request_times if t > minute_ago]

        # Check if we're at the limit
        if len(self._request_times) >= self._rate_limit_per_minute:
            return False

        # Add current request
        self._request_times.append(now)
        return True

    async def _execute_with_resilience(
        self,
        operation: Callable,
        *args,
        operation_name: str = "unknown",
        timeout_seconds: Optional[float] = None,
        **kwargs
    ) -> AdapterResponse:
        """
        Execute an operation with circuit breaker and retry logic.

        Args:
            operation: Async operation to execute
            operation_name: Name for logging
            timeout_seconds: Optional timeout override
            *args, **kwargs: Arguments for the operation

        Returns:
            AdapterResponse from the operation
        """
        start_time = time.time()

        try:
            # Check rate limiting
            if not await self._check_rate_limit():
                self.logger.warning(f"Rate limit exceeded for {operation_name}")
                return AdapterResponse.error_response(
                    error_message=f"Rate limit exceeded ({self._rate_limit_per_minute}/min)",
                    error_code="RATE_LIMIT_EXCEEDED",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            # Create retry decorator
            retry_decorator = self._create_retry_decorator()

            # Wrap operation with timeout if specified
            if timeout_seconds:
                async def timed_operation():
                    return await asyncio.wait_for(
                        operation(*args, **kwargs),
                        timeout=timeout_seconds
                    )
                operation_to_execute = timed_operation
            else:
                operation_to_execute = lambda: operation(*args, **kwargs)

            # Apply retry logic
            retried_operation = retry_decorator(operation_to_execute)

            # Execute with circuit breaker
            result = await self._circuit_breaker.call_async(retried_operation)

            response_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Successful {operation_name} in {response_time:.2f}ms")

            return result

        except CircuitBreakerError:
            error_msg = f"Circuit breaker open for {operation_name}"
            self.logger.error(error_msg)
            return AdapterResponse.error_response(
                error_message=error_msg,
                error_code="CIRCUIT_BREAKER_OPEN",
                response_time_ms=(time.time() - start_time) * 1000
            )

        except asyncio.TimeoutError:
            error_msg = f"Timeout in {operation_name} after {timeout_seconds}s"
            self.logger.error(error_msg)
            return AdapterResponse.error_response(
                error_message=error_msg,
                error_code="TIMEOUT",
                response_time_ms=(time.time() - start_time) * 1000
            )

        except RetryError as e:
            error_msg = f"All retries exhausted for {operation_name}: {e.last_attempt.exception()}"
            self.logger.error(error_msg)
            return AdapterResponse.error_response(
                error_message=error_msg,
                error_code="RETRY_EXHAUSTED",
                response_time_ms=(time.time() - start_time) * 1000
            )

        except Exception as e:
            error_msg = f"Unexpected error in {operation_name}: {str(e)}"
            self.logger.error(error_msg)
            return AdapterResponse.error_response(
                error_message=error_msg,
                error_code="UNEXPECTED_ERROR",
                response_time_ms=(time.time() - start_time) * 1000
            )

    def get_circuit_breaker_state(self) -> str:
        """
        Get current circuit breaker state.

        Returns:
            State string: 'closed', 'open', or 'half_open'
        """
        state = self._circuit_breaker.current_state
        return state.name.lower()

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dict with failure count, success count, state, etc.
        """
        return {
            "state": self.get_circuit_breaker_state(),
            "failure_count": self._circuit_breaker.fail_counter,
            "success_count": getattr(self._circuit_breaker, 'success_counter', 0),
            "last_failure_time": getattr(self._circuit_breaker, 'last_failure_time', None),
            "next_attempt_time": getattr(self._circuit_breaker, 'next_attempt_time', None)
        }

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._circuit_breaker.reset()
        self.logger.info(f"Circuit breaker reset for {self.provider_name}")

    async def force_circuit_breaker_open(self) -> None:
        """Force circuit breaker to open state (for testing/maintenance)."""
        # Simulate failures to open the circuit breaker
        for _ in range(self._circuit_breaker.fail_max):
            try:
                self._circuit_breaker.call(lambda: (_ for _ in ()).throw(AdapterError("Forced failure")))
            except:
                pass

        self.logger.info(f"Circuit breaker forced open for {self.provider_name}")


class MetricsCollectionMixin:
    """
    Mixin for collecting and tracking adapter metrics.

    Provides functionality to track request counts, latencies,
    success rates, and other performance metrics.
    """

    def __init__(self, *args, **kwargs):
        """Initialize metrics tracking."""
        super().__init__(*args, **kwargs)

        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "rate_limit_hits": 0,
            "last_request_time": None,
            "request_times": []  # Last 100 request times for percentile calculations
        }

        self.logger = logging.getLogger(f"adapter.{self.provider_name}.metrics")

    def _record_request_metrics(
        self,
        success: bool,
        latency_ms: float,
        hit_rate_limit: bool = False
    ) -> None:
        """Record metrics for a request."""
        self._metrics["total_requests"] += 1
        self._metrics["total_latency_ms"] += latency_ms
        self._metrics["last_request_time"] = datetime.utcnow()

        if success:
            self._metrics["successful_requests"] += 1
        else:
            self._metrics["failed_requests"] += 1

        if hit_rate_limit:
            self._metrics["rate_limit_hits"] += 1

        # Keep last 100 request times for percentile calculations
        self._metrics["request_times"].append(latency_ms)
        if len(self._metrics["request_times"]) > 100:
            self._metrics["request_times"].pop(0)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            Dict with all collected metrics and calculated statistics
        """
        total_requests = self._metrics["total_requests"]

        if total_requests == 0:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "error_rate": 0.0,
                "average_latency_ms": 0.0,
                "rate_limit_hits": 0,
                "last_request_time": None
            }

        success_rate = self._metrics["successful_requests"] / total_requests
        error_rate = self._metrics["failed_requests"] / total_requests
        avg_latency = self._metrics["total_latency_ms"] / total_requests

        # Calculate percentiles if we have enough data
        request_times = sorted(self._metrics["request_times"])
        percentiles = {}
        if len(request_times) >= 10:
            percentiles = {
                "p50": request_times[len(request_times) // 2],
                "p90": request_times[int(len(request_times) * 0.9)],
                "p95": request_times[int(len(request_times) * 0.95)],
                "p99": request_times[int(len(request_times) * 0.99)]
            }

        return {
            "total_requests": total_requests,
            "successful_requests": self._metrics["successful_requests"],
            "failed_requests": self._metrics["failed_requests"],
            "success_rate": success_rate,
            "error_rate": error_rate,
            "average_latency_ms": avg_latency,
            "rate_limit_hits": self._metrics["rate_limit_hits"],
            "last_request_time": self._metrics["last_request_time"],
            "latency_percentiles": percentiles
        }

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "rate_limit_hits": 0,
            "last_request_time": None,
            "request_times": []
        }
        self.logger.info(f"Metrics reset for {self.provider_name}")


class CachingMixin:
    """
    Mixin providing simple caching functionality for adapter responses.

    Implements TTL-based caching to reduce API calls for frequently
    requested data.
    """

    def __init__(self, *args, **kwargs):
        """Initialize caching."""
        super().__init__(*args, **kwargs)

        self._cache = {}
        self._cache_ttl_seconds = self.config.get("cache_ttl_seconds", 300)  # 5 minutes default
        self.logger = logging.getLogger(f"adapter.{self.provider_name}.cache")

    def _cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key for operation and parameters."""
        # Simple cache key generation - in production you'd want something more robust
        key_parts = [operation] + [str(arg) for arg in args]
        if kwargs:
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return ":".join(key_parts)

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check if cached data is still valid."""
        expiry_time = cached_at + timedelta(seconds=self._cache_ttl_seconds)
        return datetime.utcnow() < expiry_time

    def _get_from_cache(self, cache_key: str) -> Optional[AdapterResponse]:
        """Get response from cache if valid."""
        if cache_key in self._cache:
            cached_response, cached_at = self._cache[cache_key]
            if self._is_cache_valid(cached_at):
                self.logger.debug(f"Cache hit for {cache_key}")
                return cached_response
            else:
                # Remove expired entry
                del self._cache[cache_key]
                self.logger.debug(f"Cache expired for {cache_key}")

        return None

    def _store_in_cache(self, cache_key: str, response: AdapterResponse) -> None:
        """Store successful response in cache."""
        if response.success:
            self._cache[cache_key] = (response, datetime.utcnow())
            self.logger.debug(f"Cached response for {cache_key}")

    async def _execute_with_cache(
        self,
        operation: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> AdapterResponse:
        """
        Execute operation with caching.

        Args:
            operation: Operation to execute
            cache_key: Key for caching
            *args, **kwargs: Arguments for operation

        Returns:
            AdapterResponse (cached or fresh)
        """
        # Try cache first
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response

        # Execute operation
        response = await operation(*args, **kwargs)

        # Cache successful responses
        self._store_in_cache(cache_key, response)

        return response

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self.logger.info(f"Cache cleared for {self.provider_name}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        valid_entries = 0

        for cached_response, cached_at in self._cache.values():
            if self._is_cache_valid(cached_at):
                valid_entries += 1

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_ttl_seconds": self._cache_ttl_seconds
        }
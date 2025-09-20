"""
Provider manager for handling fallback chains and load balancing.

Manages multiple market data providers with automatic failover,
load balancing, and intelligent routing based on provider health
and performance metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
from sqlalchemy.orm import Session

from src.services.config_manager import ConfigurationManager
from src.services.adapters.base_adapter import MarketDataAdapter, AdapterResponse
from src.services.adapters.metrics import get_metrics_collector
from src.models.provider_configuration import ProviderConfiguration

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Status of a provider in the fallback chain."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"
    RATE_LIMITED = "rate_limited"


@dataclass
class ProviderHealth:
    """Health information for a provider."""
    provider_id: str
    status: ProviderStatus
    last_check: float
    success_rate: float
    avg_latency_ms: float
    error_count: int
    circuit_breaker_state: str


class ProviderManager:
    """
    Manages multiple market data providers with intelligent routing.

    Provides automatic failover, load balancing, and health monitoring
    across multiple provider instances.
    """

    def __init__(self, config_manager: ConfigurationManager):
        """
        Initialize provider manager.

        Args:
            config_manager: Configuration manager for provider access
        """
        self.config_manager = config_manager
        self.metrics_collector = get_metrics_collector()
        self.logger = logging.getLogger("provider.manager")

        # Provider health tracking
        self._provider_health: Dict[str, ProviderHealth] = {}
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0

        # Load balancing configuration
        self._load_balance_strategy = "priority"  # priority, round_robin, weighted
        self._round_robin_index = 0

        # Fallback configuration
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds
        self._circuit_breaker_threshold = 5  # failures before opening

    async def get_current_price(self, symbol: str, priority_provider: Optional[str] = None) -> AdapterResponse:
        """
        Get current price with automatic provider selection and fallback.

        Args:
            symbol: Stock symbol to fetch
            priority_provider: Preferred provider (optional)

        Returns:
            AdapterResponse with price data or error
        """
        request_id = f"get_price_{symbol}_{int(time.time())}"
        self.logger.info(f"Getting price for {symbol} (request: {request_id})")

        # Get available providers in priority order
        providers = await self._get_available_providers()

        if not providers:
            return AdapterResponse.error_response(
                error_message="No healthy providers available",
                error_code="NO_PROVIDERS"
            )

        # If priority provider specified, try it first
        if priority_provider:
            priority_config = next((p for p in providers if p.provider_name == priority_provider), None)
            if priority_config:
                providers.remove(priority_config)
                providers.insert(0, priority_config)

        # Try providers in order until success
        last_error = None
        for i, config in enumerate(providers):
            try:
                # Record request start
                provider_request_id = self.metrics_collector.record_request_start(
                    config.provider_name, "get_current_price"
                )

                # Get adapter instance
                adapter = await self.config_manager.get_adapter_instance(str(config.id))
                if not adapter:
                    self.logger.warning(f"Could not get adapter for {config.provider_name}")
                    continue

                # Make the request
                response = await adapter.get_current_price(symbol)

                # Record request completion
                self.metrics_collector.record_request_end(
                    provider_request_id,
                    config.provider_name,
                    "get_current_price",
                    response
                )

                if response.success:
                    # Update provider health on success
                    self._update_provider_health(str(config.id), True, response.response_time_ms or 0)

                    self.logger.info(f"Successfully fetched {symbol} from {config.provider_name}")
                    return response
                else:
                    # Track the error but continue to next provider
                    last_error = response.error_message
                    self._update_provider_health(str(config.id), False, response.response_time_ms or 0)

                    self.logger.warning(f"Provider {config.provider_name} failed: {last_error}")

            except Exception as e:
                error_msg = f"Exception with provider {config.provider_name}: {str(e)}"
                self.logger.error(error_msg)
                last_error = error_msg
                self._update_provider_health(str(config.id), False, 0)

        # All providers failed
        return AdapterResponse.error_response(
            error_message=f"All providers failed. Last error: {last_error}",
            error_code="ALL_PROVIDERS_FAILED"
        )

    async def get_multiple_prices(
        self,
        symbols: List[str],
        prefer_bulk: bool = True
    ) -> AdapterResponse:
        """
        Get multiple prices with intelligent provider selection.

        Args:
            symbols: List of symbols to fetch
            prefer_bulk: Prefer providers that support bulk requests

        Returns:
            AdapterResponse with multiple price data
        """
        request_id = f"get_multiple_prices_{len(symbols)}_{int(time.time())}"
        self.logger.info(f"Getting prices for {len(symbols)} symbols (request: {request_id})")

        # Get providers, preferring those with bulk support if requested
        providers = await self._get_available_providers()

        if prefer_bulk:
            # Sort providers by bulk capability
            bulk_providers = [p for p in providers if self._supports_bulk_quotes(p.provider_name)]
            single_providers = [p for p in providers if not self._supports_bulk_quotes(p.provider_name)]
            providers = bulk_providers + single_providers

        if not providers:
            return AdapterResponse.error_response(
                error_message="No healthy providers available",
                error_code="NO_PROVIDERS"
            )

        # Try providers until success
        for config in providers:
            try:
                provider_request_id = self.metrics_collector.record_request_start(
                    config.provider_name, "get_multiple_prices"
                )

                adapter = await self.config_manager.get_adapter_instance(str(config.id))
                if not adapter:
                    continue

                response = await adapter.get_multiple_prices(symbols)

                self.metrics_collector.record_request_end(
                    provider_request_id,
                    config.provider_name,
                    "get_multiple_prices",
                    response
                )

                if response.success:
                    self._update_provider_health(str(config.id), True, response.response_time_ms or 0)
                    self.logger.info(f"Successfully fetched {len(symbols)} prices from {config.provider_name}")
                    return response
                else:
                    self._update_provider_health(str(config.id), False, response.response_time_ms or 0)

            except Exception as e:
                self.logger.error(f"Exception with provider {config.provider_name}: {str(e)}")
                self._update_provider_health(str(config.id), False, 0)

        return AdapterResponse.error_response(
            error_message="All providers failed for multiple prices request",
            error_code="ALL_PROVIDERS_FAILED"
        )

    async def check_provider_health(self, config_id: str) -> ProviderHealth:
        """
        Check health of a specific provider.

        Args:
            config_id: Provider configuration ID

        Returns:
            ProviderHealth with current status
        """
        config = self.config_manager.get_provider_configuration(config_id)
        if not config:
            return ProviderHealth(
                provider_id=config_id,
                status=ProviderStatus.UNHEALTHY,
                last_check=time.time(),
                success_rate=0.0,
                avg_latency_ms=0.0,
                error_count=0,
                circuit_breaker_state="unknown"
            )

        try:
            adapter = await self.config_manager.get_adapter_instance(config_id)
            if not adapter:
                return ProviderHealth(
                    provider_id=config_id,
                    status=ProviderStatus.UNHEALTHY,
                    last_check=time.time(),
                    success_rate=0.0,
                    avg_latency_ms=0.0,
                    error_count=0,
                    circuit_breaker_state="unknown"
                )

            # Perform health check
            health_response = await adapter.health_check()

            # Get current metrics
            metrics_snapshot = self.metrics_collector.get_provider_metrics_snapshot(config.provider_name)

            # Determine status based on health check and metrics
            if health_response.success:
                if metrics_snapshot and metrics_snapshot.success_rate < 0.8:
                    status = ProviderStatus.DEGRADED
                else:
                    status = ProviderStatus.HEALTHY
            else:
                if "rate_limit" in (health_response.error_code or "").lower():
                    status = ProviderStatus.RATE_LIMITED
                elif "circuit" in (health_response.error_message or "").lower():
                    status = ProviderStatus.CIRCUIT_OPEN
                else:
                    status = ProviderStatus.UNHEALTHY

            # Create health record
            health = ProviderHealth(
                provider_id=config_id,
                status=status,
                last_check=time.time(),
                success_rate=metrics_snapshot.success_rate if metrics_snapshot else 0.0,
                avg_latency_ms=metrics_snapshot.avg_latency_ms if metrics_snapshot else 0.0,
                error_count=metrics_snapshot.error_count if metrics_snapshot else 0,
                circuit_breaker_state=metrics_snapshot.circuit_breaker_state if metrics_snapshot else "unknown"
            )

            # Cache the health status
            self._provider_health[config_id] = health

            return health

        except Exception as e:
            self.logger.error(f"Error checking health for {config_id}: {e}")
            return ProviderHealth(
                provider_id=config_id,
                status=ProviderStatus.UNHEALTHY,
                last_check=time.time(),
                success_rate=0.0,
                avg_latency_ms=0.0,
                error_count=0,
                circuit_breaker_state="error"
            )

    async def get_all_provider_health(self) -> Dict[str, ProviderHealth]:
        """Get health status for all configured providers."""
        active_configs = self.config_manager.get_active_configurations()
        health_checks = {}

        # Run health checks in parallel
        tasks = []
        for config in active_configs:
            task = self.check_provider_health(str(config.id))
            tasks.append((str(config.id), task))

        # Wait for all health checks to complete
        for config_id, task in tasks:
            try:
                health = await task
                health_checks[config_id] = health
            except Exception as e:
                self.logger.error(f"Health check failed for {config_id}: {e}")

        return health_checks

    async def _get_available_providers(self) -> List[ProviderConfiguration]:
        """Get list of available providers ordered by priority and health."""
        active_configs = self.config_manager.get_active_configurations()

        # Filter out unhealthy providers
        available_providers = []
        for config in active_configs:
            health = self._provider_health.get(str(config.id))
            if not health or health.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]:
                available_providers.append(config)

        # Sort by priority (if configured) or by health/performance
        if self._load_balance_strategy == "priority":
            # Sort by priority field in config_data, or by provider name
            available_providers.sort(key=lambda x: x.config_data.get("priority", 999))
        elif self._load_balance_strategy == "performance":
            # Sort by success rate and latency
            def performance_score(config):
                health = self._provider_health.get(str(config.id))
                if not health:
                    return 0
                # Higher success rate and lower latency = better score
                return health.success_rate - (health.avg_latency_ms / 1000)

            available_providers.sort(key=performance_score, reverse=True)

        return available_providers

    def _update_provider_health(self, config_id: str, success: bool, latency_ms: float):
        """Update provider health tracking."""
        current_health = self._provider_health.get(config_id)

        if current_health:
            # Update existing health record
            if success:
                current_health.success_rate = min(1.0, current_health.success_rate + 0.1)
                current_health.error_count = max(0, current_health.error_count - 1)
            else:
                current_health.success_rate = max(0.0, current_health.success_rate - 0.1)
                current_health.error_count += 1

            current_health.avg_latency_ms = (current_health.avg_latency_ms + latency_ms) / 2
            current_health.last_check = time.time()

    def _supports_bulk_quotes(self, provider_name: str) -> bool:
        """Check if provider supports bulk quote requests."""
        provider_info = self.config_manager.provider_registry.get_provider_info(provider_name)
        if not provider_info:
            return False

        # Get capabilities from provider
        try:
            temp_adapter = provider_info.adapter_class(provider_name, {})
            return temp_adapter.capabilities.supports_bulk_quotes
        except Exception:
            return False

    async def get_provider_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for provider configuration optimization.

        Returns:
            Dict with optimization recommendations
        """
        health_status = await self.get_all_provider_health()
        active_configs = self.config_manager.get_active_configurations()

        recommendations = {
            "total_providers": len(active_configs),
            "healthy_providers": len([h for h in health_status.values() if h.status == ProviderStatus.HEALTHY]),
            "recommendations": []
        }

        # Check for single points of failure
        if len(active_configs) < 2:
            recommendations["recommendations"].append({
                "type": "reliability",
                "priority": "high",
                "message": "Consider adding a backup provider for redundancy"
            })

        # Check for poor performing providers
        for config_id, health in health_status.items():
            if health.success_rate < 0.5:
                config = self.config_manager.get_provider_configuration(config_id)
                recommendations["recommendations"].append({
                    "type": "performance",
                    "priority": "medium",
                    "message": f"Provider {config.display_name if config else config_id} has low success rate ({health.success_rate:.1%})"
                })

        # Check for cost optimization opportunities
        # This would require cost data analysis
        recommendations["recommendations"].append({
            "type": "cost",
            "priority": "low",
            "message": "Review provider costs and usage patterns for optimization opportunities"
        })

        return recommendations

    async def cleanup(self):
        """Clean up provider manager resources."""
        # Clear health cache
        self._provider_health.clear()
        self.logger.info("Provider manager cleanup complete")


# Global provider manager instance
_provider_manager: Optional[ProviderManager] = None


def get_provider_manager(config_manager: Optional[ConfigurationManager] = None) -> ProviderManager:
    """Get the global provider manager instance."""
    global _provider_manager

    if _provider_manager is None:
        if config_manager is None:
            from src.services.config_manager import get_config_manager
            config_manager = get_config_manager()

        _provider_manager = ProviderManager(config_manager)

    return _provider_manager
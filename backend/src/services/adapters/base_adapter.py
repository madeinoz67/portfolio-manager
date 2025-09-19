"""
Abstract base class for market data provider adapters.

Defines the standard interface that all market data providers must implement,
ensuring consistent behavior across different data sources and enabling
easy addition of new providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio
import logging

logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception for adapter-related errors."""

    def __init__(self, message: str, provider_name: str = None, error_code: str = None):
        self.message = message
        self.provider_name = provider_name
        self.error_code = error_code
        super().__init__(message)


class RateLimitError(AdapterError):
    """Raised when adapter hits rate limiting."""
    pass


class AuthenticationError(AdapterError):
    """Raised when adapter authentication fails."""
    pass


class ProviderTimeoutError(AdapterError):
    """Raised when provider request times out."""
    pass


class InvalidSymbolError(AdapterError):
    """Raised when provider doesn't recognize a symbol."""
    pass


@dataclass
class AdapterResponse:
    """Standard response format for all adapter operations."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    response_time_ms: Optional[float] = None
    rate_limit_remaining: Optional[int] = None
    provider_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success_response(
        cls,
        data: Dict[str, Any],
        response_time_ms: float,
        rate_limit_remaining: int = None,
        provider_metadata: Dict[str, Any] = None
    ) -> "AdapterResponse":
        """Create a successful response."""
        return cls(
            success=True,
            data=data,
            response_time_ms=response_time_ms,
            rate_limit_remaining=rate_limit_remaining,
            provider_metadata=provider_metadata or {}
        )

    @classmethod
    def error_response(
        cls,
        error_message: str,
        error_code: str = None,
        response_time_ms: float = None,
        provider_metadata: Dict[str, Any] = None
    ) -> "AdapterResponse":
        """Create an error response."""
        return cls(
            success=False,
            error_message=error_message,
            error_code=error_code,
            response_time_ms=response_time_ms,
            provider_metadata=provider_metadata or {}
        )


@dataclass
class ProviderCapabilities:
    """Describes the capabilities of a market data provider."""

    supports_real_time: bool = False
    supports_historical: bool = True
    supports_bulk_quotes: bool = False
    max_symbols_per_request: int = 1
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_day: Optional[int] = None
    supports_intraday: bool = False
    supports_options: bool = False
    supports_crypto: bool = False


@dataclass
class CostInformation:
    """Provider cost and pricing information."""

    cost_per_call: Optional[Decimal] = None
    cost_model: str = "unknown"  # per_call, subscription, freemium, free
    monthly_quota: Optional[int] = None
    burst_quota: Optional[int] = None
    overage_cost: Optional[Decimal] = None


class MarketDataAdapter(ABC):
    """
    Abstract base class for all market data provider adapters.

    This class defines the standard interface that all market data providers
    must implement to ensure consistent behavior and enable the adapter
    pattern for easy provider switching and configuration.
    """

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        """
        Initialize the adapter with provider configuration.

        Args:
            provider_name: Unique identifier for this provider
            config: Provider-specific configuration dictionary
        """
        self.provider_name = provider_name
        self.config = config
        self.logger = logging.getLogger(f"adapter.{provider_name}")
        self._session = None  # For HTTP session management

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return the capabilities of this provider."""
        pass

    @property
    @abstractmethod
    def cost_info(self) -> CostInformation:
        """Return cost and pricing information for this provider."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the adapter and validate configuration.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def health_check(self) -> AdapterResponse:
        """
        Perform a health check to verify provider connectivity.

        Returns:
            AdapterResponse with health status
        """
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> AdapterResponse:
        """
        Get the current price for a single symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL")

        Returns:
            AdapterResponse with price data including:
            - current_price: Decimal
            - currency: str
            - last_updated: datetime
            - volume: Optional[int]
            - market_cap: Optional[Decimal]
        """
        pass

    @abstractmethod
    async def get_multiple_prices(self, symbols: List[str]) -> AdapterResponse:
        """
        Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            AdapterResponse with dict of symbol -> price data
        """
        pass

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> AdapterResponse:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (1d, 1h, etc.)

        Returns:
            AdapterResponse with historical data

        Note:
            This is optional - providers that don't support historical data
            should return an error response.
        """
        return AdapterResponse.error_response(
            f"Historical data not supported by {self.provider_name}",
            error_code="NOT_SUPPORTED"
        )

    async def validate_symbols(self, symbols: List[str]) -> AdapterResponse:
        """
        Validate that symbols are recognized by this provider.

        Args:
            symbols: List of symbols to validate

        Returns:
            AdapterResponse with validation results
        """
        return AdapterResponse.success_response(
            data={"valid_symbols": symbols, "invalid_symbols": []},
            response_time_ms=0.0
        )

    async def get_rate_limit_status(self) -> AdapterResponse:
        """
        Get current rate limit status and remaining quota.

        Returns:
            AdapterResponse with rate limit information
        """
        return AdapterResponse.success_response(
            data={
                "requests_remaining": None,
                "reset_time": None,
                "quota_used_percent": 0.0
            },
            response_time_ms=0.0
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for this adapter's configuration.

        Returns:
            JSON schema dict describing required/optional config fields
        """
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "API key for authentication"},
                "base_url": {"type": "string", "description": "Base URL for API requests"},
                "timeout": {"type": "number", "description": "Request timeout in seconds", "default": 30},
                "rate_limit": {"type": "number", "description": "Custom rate limit override"}
            },
            "required": ["api_key"]
        }

    def get_example_configuration(self) -> Dict[str, Any]:
        """
        Return example configuration for this adapter.

        Returns:
            Example configuration dict
        """
        return {
            "api_key": "your_api_key_here",
            "base_url": "https://api.provider.com",
            "timeout": 30,
            "rate_limit": 60
        }

    async def cleanup(self) -> None:
        """
        Clean up resources (close connections, etc.).

        Should be called when the adapter is no longer needed.
        """
        if self._session:
            await self._session.close()
            self._session = None

    def __str__(self) -> str:
        return f"MarketDataAdapter({self.provider_name})"

    def __repr__(self) -> str:
        return f"MarketDataAdapter(provider_name='{self.provider_name}', capabilities={self.capabilities})"
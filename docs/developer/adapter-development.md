# Adapter Development Guide

## Overview

This guide provides comprehensive information for developers who want to create new market data provider adapters or extend the existing adapter system. The adapter framework is designed to be extensible, testable, and maintainable.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adapter Interface](#adapter-interface)
3. [Creating a New Adapter](#creating-a-new-adapter)
4. [Configuration Management](#configuration-management)
5. [Metrics and Monitoring](#metrics-and-monitoring)
6. [Error Handling](#error-handling)
7. [Testing](#testing)
8. [Integration](#integration)
9. [Best Practices](#best-practices)
10. [Examples](#examples)

## Architecture Overview

### Components

The adapter system consists of several key components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Adapter System                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Admin API      │  │  Provider       │  │  Metrics     │ │
│  │  Endpoints      │  │  Registry       │  │  Collector   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Config         │  │  Health         │  │  Provider    │ │
│  │  Manager        │  │  Checker        │  │  Manager     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Base Adapter   │  │  Concrete       │  │  Resilience  │ │
│  │  (Abstract)     │  │  Adapters       │  │  Mixins      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Configuration**: Adapters are configured through the admin API
2. **Registration**: Providers register their adapter classes with the registry
3. **Instantiation**: Provider manager creates adapter instances based on configuration
4. **Execution**: Adapters fetch market data and report metrics
5. **Monitoring**: Health checker monitors adapter status and performance

## Adapter Interface

### Base Adapter Class

All adapters must inherit from the `MarketDataAdapter` abstract base class:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.services.adapters.base_adapter import MarketDataAdapter, ProviderCapabilities

class MyCustomAdapter(MarketDataAdapter):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique provider name."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the provider."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the provider."""
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch current price for a single symbol."""
        pass

    @abstractmethod
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch current prices for multiple symbols."""
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the adapter configuration."""
        pass
```

### Required Methods

#### `provider_name`
- **Type**: Property returning `str`
- **Purpose**: Unique identifier for the provider
- **Example**: `"alpha_vantage"`, `"yahoo_finance"`

#### `capabilities`
- **Type**: Property returning `ProviderCapabilities`
- **Purpose**: Describes what the provider supports
- **Fields**:
  - `supports_real_time`: Real-time data availability
  - `supports_historical`: Historical data availability
  - `supports_bulk`: Bulk request support
  - `max_symbols_per_request`: Maximum symbols per bulk request
  - `rate_limit_per_minute`: Rate limit (requests per minute)
  - `requires_api_key`: Whether API authentication is required

#### `connect()` / `disconnect()`
- **Purpose**: Manage provider connections
- **Returns**: `connect()` returns `bool` indicating success
- **Usage**: Initialize sessions, authenticate, cleanup resources

#### `get_current_price()`
- **Purpose**: Fetch real-time price for a single symbol
- **Parameters**: `symbol: str` - Stock symbol (e.g., "AAPL")
- **Returns**: Dictionary with price data
- **Required Fields**:
  ```python
  {
      "symbol": str,           # Stock symbol
      "price": Decimal,        # Current price
      "volume": int,           # Trading volume
      "market_cap": Decimal,   # Market capitalization
      "timestamp": str,        # ISO format timestamp
      "source": str            # Provider name
  }
  ```

#### `get_multiple_prices()`
- **Purpose**: Fetch real-time prices for multiple symbols
- **Parameters**: `symbols: List[str]` - List of stock symbols
- **Returns**: Dictionary mapping symbols to price data or None
- **Example**:
  ```python
  {
      "AAPL": {"symbol": "AAPL", "price": Decimal("150.25"), ...},
      "MSFT": {"symbol": "MSFT", "price": Decimal("280.50"), ...},
      "INVALID": None  # Failed to fetch
  }
  ```

#### `validate_config()`
- **Purpose**: Validate adapter configuration
- **Returns**: `bool` indicating if configuration is valid
- **Should Check**: API keys, URLs, required fields, authentication

## Creating a New Adapter

### Step 1: Create Adapter Class

Create a new file in `backend/src/services/adapters/providers/`:

```python
# backend/src/services/adapters/providers/my_provider.py

import aiohttp
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.services.adapters.base_adapter import (
    MarketDataAdapter,
    ProviderCapabilities,
    AdapterError,
    AdapterConnectionError,
    AdapterRateLimitError,
    AdapterValidationError,
)

class MyProviderAdapter(MarketDataAdapter):
    """Adapter for My Custom Provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.myprovider.com/v1')
        self.timeout = config.get('timeout', 30)
        self.session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_name(self) -> str:
        return "my_provider"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk=True,
            max_symbols_per_request=50,
            rate_limit_per_minute=100,
            requires_api_key=True
        )

    async def connect(self) -> bool:
        """Establish connection to My Provider API."""
        try:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'User-Agent': 'PortfolioManager/1.0'
                }
            )

            # Test connection
            async with self.session.get(f'{self.base_url}/status') as response:
                if response.status == 200:
                    return True
                else:
                    raise AdapterConnectionError(f"Connection test failed: {response.status}")

        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            raise AdapterConnectionError(f"Failed to connect: {str(e)}")

    async def disconnect(self) -> None:
        """Close connection to My Provider API."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch current price for a symbol."""
        if not self.session:
            raise AdapterConnectionError("Not connected to provider")

        try:
            url = f"{self.base_url}/quote"
            params = {"symbol": symbol}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_price_data(data)
                elif response.status == 429:
                    raise AdapterRateLimitError("Rate limit exceeded")
                else:
                    raise AdapterError(f"API error: {response.status}")

        except aiohttp.ClientError as e:
            raise AdapterConnectionError(f"Network error: {str(e)}")

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch current prices for multiple symbols."""
        if not self.session:
            raise AdapterConnectionError("Not connected to provider")

        # Check bulk limit
        if len(symbols) > self.capabilities.max_symbols_per_request:
            raise AdapterValidationError(
                f"Too many symbols: {len(symbols)} > {self.capabilities.max_symbols_per_request}"
            )

        try:
            url = f"{self.base_url}/quotes"
            data = {"symbols": symbols}

            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    api_data = await response.json()
                    return self._parse_multiple_price_data(api_data)
                elif response.status == 429:
                    raise AdapterRateLimitError("Rate limit exceeded")
                else:
                    raise AdapterError(f"Bulk API error: {response.status}")

        except aiohttp.ClientError as e:
            raise AdapterConnectionError(f"Network error: {str(e)}")

    async def validate_config(self) -> bool:
        """Validate adapter configuration."""
        if not self.api_key:
            raise AdapterValidationError("API key is required")

        if not self.base_url.startswith(('http://', 'https://')):
            raise AdapterValidationError("Invalid base URL format")

        if self.timeout <= 0:
            raise AdapterValidationError("Timeout must be positive")

        return True

    def _parse_price_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse API response into standard format."""
        return {
            "symbol": data["symbol"],
            "price": Decimal(str(data["price"])),
            "volume": int(data["volume"]),
            "market_cap": Decimal(str(data.get("market_cap", 0))),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": self.provider_name
        }

    def _parse_multiple_price_data(self, data: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Parse bulk API response into standard format."""
        results = {}
        for symbol_data in data.get("quotes", []):
            try:
                symbol = symbol_data["symbol"]
                results[symbol] = self._parse_price_data(symbol_data)
            except (KeyError, ValueError):
                results[symbol_data.get("symbol", "UNKNOWN")] = None
        return results
```

### Step 2: Register the Adapter

Add registration in `backend/src/services/adapters/registry.py`:

```python
# Import your adapter
from src.services.adapters.providers.my_provider import MyProviderAdapter

def initialize_default_providers(registry: ProviderRegistry) -> None:
    """Initialize default market data providers."""
    try:
        # Existing providers...

        # Register your new adapter
        registry.register_provider("my_provider", MyProviderAdapter)

    except Exception as e:
        logger.error(f"Failed to initialize providers: {e}")
```

### Step 3: Add Configuration Validation

Update `backend/src/services/config_manager.py`:

```python
def _validate_my_provider_config(self, config: Dict[str, Any]) -> ValidationResult:
    """Validate My Provider configuration."""
    result = ValidationResult()

    # Required fields
    required_fields = ["api_key"]
    result.errors.extend(self._validate_required_fields(config, required_fields))

    # API key format validation
    api_key = config.get("api_key", "")
    if api_key and len(api_key) < 20:
        result.errors.append("API key appears to be too short")

    # URL validation
    base_url = config.get("base_url", "")
    if base_url and not self._is_valid_url(base_url):
        result.errors.append("Invalid base URL format")

    # Timeout validation
    timeout = config.get("timeout")
    if timeout is not None:
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            result.errors.append("Timeout must be a positive number")
        elif timeout > 120:
            result.warnings.append("Timeout is quite high (>120 seconds)")

    result.is_valid = len(result.errors) == 0
    return result
```

### Step 4: Add Provider to Frontend

Update `frontend/src/components/Admin/Adapters/AdapterConfigForm.tsx`:

```typescript
const getProviderDisplayName = (providerName: string) => {
  const displayNames: Record<string, string> = {
    // Existing providers...
    'my_provider': 'My Custom Provider',
  };
  return displayNames[providerName] || providerName;
};

const getProviderConfigFields = (providerName: string) => {
  switch (providerName) {
    // Existing cases...

    case 'my_provider':
      return (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="api_key">API Key *</Label>
              <Input
                id="api_key"
                type="password"
                {...register('config.api_key')}
                placeholder="Enter your My Provider API key"
              />
              {errors.config?.api_key && (
                <p className="text-sm text-red-600">{errors.config.api_key.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="base_url">Base URL</Label>
              <Input
                id="base_url"
                {...register('config.base_url')}
                placeholder="https://api.myprovider.com/v1"
              />
            </div>

            <div>
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                {...register('config.timeout', { valueAsNumber: true })}
                placeholder="30"
              />
            </div>
          </div>
        </>
      );

    default:
      return <p>Select a provider to configure settings</p>;
  }
};
```

## Configuration Management

### Configuration Schema

Define configuration requirements for your adapter:

```python
class MyProviderConfig:
    """Configuration schema for My Provider."""

    REQUIRED_FIELDS = ["api_key"]
    OPTIONAL_FIELDS = ["base_url", "timeout", "max_retries"]

    DEFAULT_VALUES = {
        "base_url": "https://api.myprovider.com/v1",
        "timeout": 30,
        "max_retries": 3
    }

    @classmethod
    def validate(cls, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return error messages."""
        errors = []

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in config or not config[field]:
                errors.append(f"{field} is required")

        # Validate API key format
        api_key = config.get("api_key", "")
        if api_key and not cls._is_valid_api_key(api_key):
            errors.append("Invalid API key format")

        return errors

    @classmethod
    def _is_valid_api_key(cls, api_key: str) -> bool:
        """Validate API key format."""
        return len(api_key) >= 20 and api_key.isalnum()
```

### Environment Variables

Support environment variable configuration:

```python
import os

class MyProviderAdapter(MarketDataAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Support environment variable fallbacks
        self.api_key = config.get('api_key') or os.getenv('MY_PROVIDER_API_KEY')
        self.base_url = config.get('base_url') or os.getenv('MY_PROVIDER_BASE_URL', 'https://api.myprovider.com/v1')
        self.timeout = config.get('timeout', int(os.getenv('MY_PROVIDER_TIMEOUT', '30')))
```

## Metrics and Monitoring

### Automatic Metrics Collection

Metrics are automatically collected for all adapters. The base class handles:

- Request counts (total, successful, failed)
- Response times
- Error rates
- Cost tracking

### Custom Metrics

Add custom metrics specific to your provider:

```python
class MyProviderAdapter(MarketDataAdapter):
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        start_time = time.perf_counter()

        try:
            result = await self._fetch_price_data(symbol)

            # Record custom metrics
            response_time = (time.perf_counter() - start_time) * 1000
            await self._record_custom_metrics(symbol, response_time, success=True)

            return result

        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            await self._record_custom_metrics(symbol, response_time, success=False, error=str(e))
            raise

    async def _record_custom_metrics(self, symbol: str, response_time: float, success: bool, error: str = None):
        """Record provider-specific metrics."""
        metrics_data = {
            "provider_id": self.provider_name,
            "adapter_id": self.adapter_id,
            "symbol": symbol,
            "response_time_ms": response_time,
            "success": success,
            "timestamp": datetime.now(timezone.utc),
        }

        if error:
            metrics_data["error_type"] = type(error).__name__
            metrics_data["error_message"] = str(error)

        # Store custom metrics (implementation depends on metrics storage)
        await self._store_metrics(metrics_data)
```

### Health Checks

Implement custom health checks:

```python
class MyProviderAdapter(MarketDataAdapter):
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        checks = []
        overall_status = "healthy"

        # Connectivity check
        connectivity_check = await self._check_connectivity()
        checks.append(connectivity_check)

        # Authentication check
        auth_check = await self._check_authentication()
        checks.append(auth_check)

        # Rate limit check
        rate_limit_check = await self._check_rate_limits()
        checks.append(rate_limit_check)

        # Determine overall status
        if any(check["status"] == "critical" for check in checks):
            overall_status = "down"
        elif any(check["status"] == "warning" for check in checks):
            overall_status = "degraded"

        return {
            "adapter_id": self.adapter_id,
            "provider_name": self.provider_name,
            "overall_status": overall_status,
            "last_check_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }

    async def _check_connectivity(self) -> Dict[str, Any]:
        """Check provider API connectivity."""
        try:
            start_time = time.perf_counter()

            async with self.session.get(f'{self.base_url}/status') as response:
                response_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    return {
                        "check_type": "connectivity",
                        "status": "healthy",
                        "message": "Connection successful",
                        "response_time_ms": response_time,
                        "checked_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    return {
                        "check_type": "connectivity",
                        "status": "critical",
                        "message": f"HTTP {response.status}",
                        "response_time_ms": response_time,
                        "checked_at": datetime.now(timezone.utc).isoformat()
                    }

        except Exception as e:
            return {
                "check_type": "connectivity",
                "status": "critical",
                "message": f"Connection failed: {str(e)}",
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
```

## Error Handling

### Exception Hierarchy

Use the provided exception hierarchy:

```python
from src.services.adapters.base_adapter import (
    AdapterError,              # Base exception
    AdapterConnectionError,    # Network/connection issues
    AdapterAuthenticationError,# Authentication failures
    AdapterRateLimitError,     # Rate limiting
    AdapterValidationError,    # Configuration/validation
    AdapterTimeoutError,       # Request timeouts
)

class MyProviderAdapter(MarketDataAdapter):
    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        try:
            return await self._fetch_price(symbol)
        except aiohttp.ClientTimeout:
            raise AdapterTimeoutError(f"Request timeout for {symbol}")
        except aiohttp.ClientConnectionError as e:
            raise AdapterConnectionError(f"Connection failed: {str(e)}")
        except ValueError as e:
            raise AdapterValidationError(f"Invalid symbol format: {symbol}")
```

### Retry Logic

Implement intelligent retry logic:

```python
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

class MyProviderAdapter(MarketDataAdapter):
    async def _retry_with_backoff(
        self,
        func: Callable[..., T],
        max_retries: int = 3,
        base_delay: float = 1.0,
        *args,
        **kwargs
    ) -> T:
        """Execute function with exponential backoff retry."""

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except AdapterRateLimitError:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            except AdapterConnectionError:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            except AdapterError:
                # Don't retry for other adapter errors
                raise

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        return await self._retry_with_backoff(self._fetch_price_internal, symbol=symbol)
```

## Testing

### Unit Tests

Create comprehensive unit tests:

```python
# tests/unit/test_my_provider_adapter.py

import pytest
from unittest.mock import AsyncMock, patch
import aiohttp
from decimal import Decimal

from src.services.adapters.providers.my_provider import MyProviderAdapter
from src.services.adapters.base_adapter import (
    AdapterConnectionError,
    AdapterRateLimitError,
    AdapterValidationError,
)

class TestMyProviderAdapter:
    @pytest.fixture
    def adapter_config(self):
        return {
            "api_key": "test_api_key_12345",
            "base_url": "https://api.test.com",
            "timeout": 30
        }

    @pytest.fixture
    def adapter(self, adapter_config):
        return MyProviderAdapter(adapter_config)

    def test_provider_name(self, adapter):
        assert adapter.provider_name == "my_provider"

    def test_capabilities(self, adapter):
        caps = adapter.capabilities
        assert caps.supports_real_time is True
        assert caps.supports_bulk is True
        assert caps.max_symbols_per_request == 50
        assert caps.requires_api_key is True

    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await adapter.connect()
            assert result is True
            assert adapter.session is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(AdapterConnectionError):
                await adapter.connect()

    @pytest.mark.asyncio
    async def test_get_current_price_success(self, adapter):
        # Mock successful API response
        mock_data = {
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 1000000,
            "market_cap": 2500000000000
        }

        with patch.object(adapter, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_data
            mock_session.get.return_value.__aenter__.return_value = mock_response

            result = await adapter.get_current_price("AAPL")

            assert result["symbol"] == "AAPL"
            assert result["price"] == Decimal("150.25")
            assert result["volume"] == 1000000
            assert result["source"] == "my_provider"

    @pytest.mark.asyncio
    async def test_get_current_price_rate_limit(self, adapter):
        with patch.object(adapter, 'session') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_session.get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(AdapterRateLimitError):
                await adapter.get_current_price("AAPL")

    @pytest.mark.asyncio
    async def test_validate_config_success(self, adapter):
        result = await adapter.validate_config()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_config_missing_api_key(self):
        config = {"base_url": "https://api.test.com"}
        adapter = MyProviderAdapter(config)

        with pytest.raises(AdapterValidationError, match="API key is required"):
            await adapter.validate_config()
```

### Integration Tests

Test the complete adapter integration:

```python
# tests/integration/test_my_provider_integration.py

import pytest
from src.services.adapters.registry import ProviderRegistry
from src.services.adapters.providers.my_provider import MyProviderAdapter

class TestMyProviderIntegration:
    @pytest.fixture
    def registry(self):
        registry = ProviderRegistry()
        registry.register_provider("my_provider", MyProviderAdapter)
        return registry

    def test_adapter_registration(self, registry):
        assert "my_provider" in registry.list_providers()
        assert registry.is_provider_registered("my_provider")

    def test_adapter_creation(self, registry):
        config = {
            "api_key": "test_key",
            "base_url": "https://api.test.com"
        }

        adapter = registry.create_adapter("my_provider", config)
        assert isinstance(adapter, MyProviderAdapter)
        assert adapter.provider_name == "my_provider"

    def test_capabilities_access(self, registry):
        caps = registry.get_provider_capabilities("my_provider")
        assert caps.supports_real_time is True
        assert caps.requires_api_key is True
```

### Contract Tests

Ensure your adapter meets the contract requirements:

```python
# tests/contract/test_my_provider_contract.py

import pytest
from decimal import Decimal
from datetime import datetime

class TestMyProviderContract:
    @pytest.mark.asyncio
    async def test_get_current_price_response_format(self, adapter):
        # Assuming test environment or mocked responses
        result = await adapter.get_current_price("AAPL")

        # Contract requirements
        assert "symbol" in result
        assert "price" in result
        assert "volume" in result
        assert "market_cap" in result
        assert "timestamp" in result
        assert "source" in result

        # Type validation
        assert isinstance(result["symbol"], str)
        assert isinstance(result["price"], Decimal)
        assert isinstance(result["volume"], int)
        assert isinstance(result["market_cap"], Decimal)
        assert isinstance(result["source"], str)

        # Value validation
        assert result["symbol"] == "AAPL"
        assert result["price"] > 0
        assert result["volume"] >= 0
        assert result["source"] == adapter.provider_name

        # Timestamp format validation
        timestamp = datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        assert timestamp is not None
```

## Integration

### Database Models

Your adapter configurations are automatically stored using the existing models:

- `ProviderConfiguration`: Stores adapter configuration
- `ProviderMetrics`: Stores performance metrics
- `AdapterHealthCheck`: Stores health check results

### API Endpoints

Your adapter automatically becomes available through the admin API endpoints:

- `GET /api/v1/admin/adapters` - Lists your adapter
- `POST /api/v1/admin/adapters` - Creates adapter configuration
- `GET /api/v1/admin/adapters/{id}/metrics` - Shows adapter metrics
- `GET /api/v1/admin/adapters/{id}/health` - Shows health status

### Configuration Validation

Add provider-specific validation to `ConfigValidator`:

```python
# src/services/config_manager.py

class ConfigValidator:
    def validate_provider_config(self, provider_name: str, config: Dict[str, Any]) -> ValidationResult:
        """Validate provider-specific configuration."""

        if provider_name == "my_provider":
            return self._validate_my_provider_config(config)
        # ... other providers

        result = ValidationResult()
        result.errors.append(f"Unknown provider: {provider_name}")
        result.is_valid = False
        return result
```

## Best Practices

### Performance

1. **Connection Pooling**: Use aiohttp connection pooling
2. **Async Operations**: Keep all I/O operations async
3. **Bulk Requests**: Implement efficient bulk operations
4. **Caching**: Cache frequently requested data appropriately
5. **Timeouts**: Set reasonable timeout values

### Reliability

1. **Error Handling**: Use appropriate exception types
2. **Retry Logic**: Implement exponential backoff
3. **Circuit Breakers**: Use resilience patterns for external APIs
4. **Health Checks**: Implement comprehensive health monitoring
5. **Graceful Degradation**: Handle partial failures gracefully

### Security

1. **Credential Management**: Never log sensitive information
2. **Input Validation**: Validate all inputs thoroughly
3. **Rate Limiting**: Respect provider rate limits
4. **HTTPS Only**: Always use encrypted connections
5. **Key Rotation**: Support API key rotation

### Maintainability

1. **Documentation**: Document all configuration options
2. **Logging**: Provide detailed logging for troubleshooting
3. **Testing**: Maintain high test coverage
4. **Versioning**: Handle API version changes gracefully
5. **Monitoring**: Implement comprehensive monitoring

## Examples

### Simple REST API Adapter

```python
class SimpleRestAdapter(MarketDataAdapter):
    """Example adapter for a simple REST API provider."""

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.base_url}/quote/{symbol}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "symbol": symbol,
                    "price": Decimal(str(data["last_price"])),
                    "volume": data["volume"],
                    "market_cap": Decimal(str(data.get("market_cap", 0))),
                    "timestamp": data["timestamp"],
                    "source": self.provider_name
                }
            else:
                raise AdapterError(f"API error: {response.status}")
```

### WebSocket Adapter Template

```python
class WebSocketAdapter(MarketDataAdapter):
    """Example adapter for WebSocket-based providers."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.websocket = None
        self.price_cache = {}

    async def connect(self) -> bool:
        """Connect to WebSocket stream."""
        try:
            self.websocket = await websockets.connect(
                self.websocket_url,
                extra_headers={"Authorization": f"Bearer {self.api_key}"}
            )

            # Start background task to handle messages
            asyncio.create_task(self._handle_websocket_messages())
            return True
        except Exception as e:
            raise AdapterConnectionError(f"WebSocket connection failed: {str(e)}")

    async def _handle_websocket_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data.get("type") == "price_update":
                    symbol = data["symbol"]
                    self.price_cache[symbol] = {
                        "symbol": symbol,
                        "price": Decimal(str(data["price"])),
                        "volume": data["volume"],
                        "timestamp": data["timestamp"],
                        "source": self.provider_name
                    }
        except websockets.exceptions.ConnectionClosed:
            # Handle reconnection logic
            await self._reconnect()

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get price from cache or request update."""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        else:
            # Subscribe to symbol and wait for update
            await self._subscribe_symbol(symbol)
            # Implementation depends on your specific requirements
```

---

This guide provides the foundation for creating robust, maintainable market data adapters. Remember to follow the established patterns and contribute improvements back to the adapter framework as you discover new requirements or optimizations.
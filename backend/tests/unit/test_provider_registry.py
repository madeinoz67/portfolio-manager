"""
T060: Unit tests for provider registry
Tests ProviderRegistry for dynamic adapter registration and management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Type
import asyncio

from src.services.adapters.registry import (
    ProviderRegistry,
    get_provider_registry,
    AdapterRegistrationError,
    DuplicateProviderError,
    ProviderNotFoundError,
)
from src.services.adapters.base_adapter import MarketDataAdapter, ProviderCapabilities


class TestProviderRegistry:
    """Test the ProviderRegistry class."""

    class MockAdapter(MarketDataAdapter):
        """Mock adapter for testing."""

        def __init__(self, config: Dict[str, Any]):
            super().__init__(config)

        @property
        def provider_name(self) -> str:
            return "mock_provider"

        @property
        def capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                supports_real_time=True,
                supports_historical=False,
                supports_bulk=True,
                max_symbols_per_request=100,
                rate_limit_per_minute=60,
                requires_api_key=True
            )

        async def connect(self) -> bool:
            return True

        async def disconnect(self) -> None:
            pass

        async def get_current_price(self, symbol: str) -> Dict[str, Any]:
            return {"symbol": symbol, "price": 100.0}

        async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
            return {symbol: {"symbol": symbol, "price": 100.0} for symbol in symbols}

        async def validate_config(self) -> bool:
            return True

    class AnotherMockAdapter(MarketDataAdapter):
        """Another mock adapter for testing."""

        def __init__(self, config: Dict[str, Any]):
            super().__init__(config)

        @property
        def provider_name(self) -> str:
            return "another_provider"

        @property
        def capabilities(self) -> ProviderCapabilities:
            return ProviderCapabilities(
                supports_real_time=False,
                supports_historical=True,
                supports_bulk=False,
                max_symbols_per_request=1,
                rate_limit_per_minute=10,
                requires_api_key=False
            )

        async def connect(self) -> bool:
            return True

        async def disconnect(self) -> None:
            pass

        async def get_current_price(self, symbol: str) -> Dict[str, Any]:
            return {"symbol": symbol, "price": 200.0}

        async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
            return {symbol: {"symbol": symbol, "price": 200.0} for symbol in symbols}

        async def validate_config(self) -> bool:
            return True

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ProviderRegistry()

        assert len(registry.list_providers()) == 0
        assert registry.get_provider_count() == 0

    def test_register_provider_success(self):
        """Test successful provider registration."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)

        assert "mock_provider" in registry.list_providers()
        assert registry.get_provider_count() == 1

    def test_register_provider_duplicate(self):
        """Test registration of duplicate provider."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)

        with pytest.raises(DuplicateProviderError, match="Provider 'mock_provider' is already registered"):
            registry.register_provider("mock_provider", self.MockAdapter)

    def test_register_provider_invalid_class(self):
        """Test registration with invalid adapter class."""
        registry = ProviderRegistry()

        class InvalidAdapter:
            pass

        with pytest.raises(AdapterRegistrationError, match="Provider class must inherit from MarketDataAdapter"):
            registry.register_provider("invalid", InvalidAdapter)

    def test_unregister_provider_success(self):
        """Test successful provider unregistration."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        assert "mock_provider" in registry.list_providers()

        registry.unregister_provider("mock_provider")
        assert "mock_provider" not in registry.list_providers()
        assert registry.get_provider_count() == 0

    def test_unregister_provider_not_found(self):
        """Test unregistration of non-existent provider."""
        registry = ProviderRegistry()

        with pytest.raises(ProviderNotFoundError, match="Provider 'nonexistent' not found"):
            registry.unregister_provider("nonexistent")

    def test_get_provider_class_success(self):
        """Test successful provider class retrieval."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)

        provider_class = registry.get_provider_class("mock_provider")
        assert provider_class == self.MockAdapter

    def test_get_provider_class_not_found(self):
        """Test provider class retrieval for non-existent provider."""
        registry = ProviderRegistry()

        with pytest.raises(ProviderNotFoundError, match="Provider 'nonexistent' not found"):
            registry.get_provider_class("nonexistent")

    def test_create_adapter_success(self):
        """Test successful adapter creation."""
        registry = ProviderRegistry()
        registry.register_provider("mock_provider", self.MockAdapter)

        config = {"api_key": "test_key", "base_url": "https://api.test.com"}
        adapter = registry.create_adapter("mock_provider", config)

        assert isinstance(adapter, self.MockAdapter)
        assert adapter.config == config
        assert adapter.provider_name == "mock_provider"

    def test_create_adapter_provider_not_found(self):
        """Test adapter creation for non-existent provider."""
        registry = ProviderRegistry()

        config = {"api_key": "test_key"}

        with pytest.raises(ProviderNotFoundError, match="Provider 'nonexistent' not found"):
            registry.create_adapter("nonexistent", config)

    def test_create_adapter_initialization_error(self):
        """Test adapter creation with initialization error."""
        registry = ProviderRegistry()

        class FailingAdapter(MarketDataAdapter):
            def __init__(self, config: Dict[str, Any]):
                raise ValueError("Initialization failed")

            @property
            def provider_name(self) -> str:
                return "failing_provider"

            @property
            def capabilities(self) -> ProviderCapabilities:
                return ProviderCapabilities()

        registry.register_provider("failing_provider", FailingAdapter)

        config = {"api_key": "test_key"}

        with pytest.raises(AdapterRegistrationError, match="Failed to create adapter instance"):
            registry.create_adapter("failing_provider", config)

    def test_list_providers_empty(self):
        """Test listing providers when registry is empty."""
        registry = ProviderRegistry()

        providers = registry.list_providers()
        assert providers == []

    def test_list_providers_multiple(self):
        """Test listing multiple registered providers."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        registry.register_provider("another_provider", self.AnotherMockAdapter)

        providers = registry.list_providers()
        assert len(providers) == 2
        assert "mock_provider" in providers
        assert "another_provider" in providers

    def test_get_provider_capabilities(self):
        """Test getting provider capabilities."""
        registry = ProviderRegistry()
        registry.register_provider("mock_provider", self.MockAdapter)

        capabilities = registry.get_provider_capabilities("mock_provider")

        assert capabilities.supports_real_time is True
        assert capabilities.supports_historical is False
        assert capabilities.supports_bulk is True
        assert capabilities.max_symbols_per_request == 100
        assert capabilities.rate_limit_per_minute == 60
        assert capabilities.requires_api_key is True

    def test_get_provider_capabilities_not_found(self):
        """Test getting capabilities for non-existent provider."""
        registry = ProviderRegistry()

        with pytest.raises(ProviderNotFoundError, match="Provider 'nonexistent' not found"):
            registry.get_provider_capabilities("nonexistent")

    def test_is_provider_registered(self):
        """Test checking if provider is registered."""
        registry = ProviderRegistry()

        assert registry.is_provider_registered("mock_provider") is False

        registry.register_provider("mock_provider", self.MockAdapter)

        assert registry.is_provider_registered("mock_provider") is True

    def test_get_providers_by_capability(self):
        """Test filtering providers by capabilities."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        registry.register_provider("another_provider", self.AnotherMockAdapter)

        # Get providers that support real-time
        real_time_providers = registry.get_providers_by_capability("supports_real_time", True)
        assert "mock_provider" in real_time_providers
        assert "another_provider" not in real_time_providers

        # Get providers that support historical
        historical_providers = registry.get_providers_by_capability("supports_historical", True)
        assert "mock_provider" not in historical_providers
        assert "another_provider" in historical_providers

        # Get providers that support bulk
        bulk_providers = registry.get_providers_by_capability("supports_bulk", True)
        assert "mock_provider" in bulk_providers
        assert "another_provider" not in bulk_providers

    def test_get_providers_by_capability_invalid_attribute(self):
        """Test filtering providers by invalid capability attribute."""
        registry = ProviderRegistry()
        registry.register_provider("mock_provider", self.MockAdapter)

        providers = registry.get_providers_by_capability("invalid_capability", True)
        assert providers == []

    def test_clear_registry(self):
        """Test clearing all providers from registry."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        registry.register_provider("another_provider", self.AnotherMockAdapter)

        assert registry.get_provider_count() == 2

        registry.clear()

        assert registry.get_provider_count() == 0
        assert len(registry.list_providers()) == 0

    def test_registry_thread_safety(self):
        """Test registry thread safety with concurrent operations."""
        import threading
        import time

        registry = ProviderRegistry()
        errors = []

        def register_provider(provider_name: str):
            try:
                registry.register_provider(provider_name, self.MockAdapter)
            except Exception as e:
                errors.append(e)

        def unregister_provider(provider_name: str):
            try:
                time.sleep(0.01)  # Small delay to create race condition
                registry.unregister_provider(provider_name)
            except Exception as e:
                errors.append(e)

        # Create threads for concurrent registration and unregistration
        threads = []
        for i in range(5):
            provider_name = f"provider_{i}"

            # Register
            t1 = threading.Thread(target=register_provider, args=(provider_name,))
            threads.append(t1)

            # Unregister
            t2 = threading.Thread(target=unregister_provider, args=(provider_name,))
            threads.append(t2)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Check that no unexpected errors occurred
        # Some ProviderNotFoundError exceptions are expected due to race conditions
        unexpected_errors = [e for e in errors if not isinstance(e, ProviderNotFoundError)]
        assert len(unexpected_errors) == 0

    def test_registry_string_representation(self):
        """Test registry string representation."""
        registry = ProviderRegistry()

        # Empty registry
        registry_str = str(registry)
        assert "ProviderRegistry" in registry_str
        assert "0 providers" in registry_str

        # Registry with providers
        registry.register_provider("mock_provider", self.MockAdapter)
        registry_str = str(registry)
        assert "1 providers" in registry_str

    def test_registry_iteration(self):
        """Test registry iteration over providers."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        registry.register_provider("another_provider", self.AnotherMockAdapter)

        provider_names = list(registry)
        assert len(provider_names) == 2
        assert "mock_provider" in provider_names
        assert "another_provider" in provider_names

    def test_registry_context_manager(self):
        """Test registry as context manager."""
        registry = ProviderRegistry()

        with registry:
            registry.register_provider("mock_provider", self.MockAdapter)
            assert registry.get_provider_count() == 1

        # Registry should still contain providers after context exit
        assert registry.get_provider_count() == 1

    def test_get_provider_registry_singleton(self):
        """Test global provider registry singleton."""
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()

        # Should return the same instance
        assert registry1 is registry2

        # Test that it's actually a ProviderRegistry instance
        assert isinstance(registry1, ProviderRegistry)

    def test_get_provider_registry_with_initialization(self):
        """Test global provider registry initialization."""
        # Clear any existing global registry
        import src.services.adapters.registry as registry_module
        if hasattr(registry_module, '_global_registry'):
            delattr(registry_module, '_global_registry')

        registry = get_provider_registry()

        # Should have some default providers registered
        # (This depends on the actual implementation - adjust as needed)
        assert isinstance(registry, ProviderRegistry)

    def test_registry_export_import(self):
        """Test registry export and import functionality."""
        registry = ProviderRegistry()

        registry.register_provider("mock_provider", self.MockAdapter)
        registry.register_provider("another_provider", self.AnotherMockAdapter)

        # Export provider information
        exported_data = registry.export_registry()

        assert len(exported_data) == 2
        assert "mock_provider" in exported_data
        assert "another_provider" in exported_data

        # Check exported data structure
        mock_data = exported_data["mock_provider"]
        assert "class_name" in mock_data
        assert "capabilities" in mock_data

    def test_registry_provider_validation(self):
        """Test provider validation during registration."""
        registry = ProviderRegistry()

        # Test with None class
        with pytest.raises(AdapterRegistrationError):
            registry.register_provider("invalid", None)

        # Test with invalid provider name
        with pytest.raises(AdapterRegistrationError):
            registry.register_provider("", self.MockAdapter)

        with pytest.raises(AdapterRegistrationError):
            registry.register_provider(None, self.MockAdapter)

    def test_registry_bulk_operations(self):
        """Test bulk registration and unregistration operations."""
        registry = ProviderRegistry()

        providers = {
            "mock_provider": self.MockAdapter,
            "another_provider": self.AnotherMockAdapter
        }

        # Bulk register
        registry.register_multiple_providers(providers)

        assert registry.get_provider_count() == 2
        assert "mock_provider" in registry.list_providers()
        assert "another_provider" in registry.list_providers()

        # Bulk unregister
        registry.unregister_multiple_providers(["mock_provider", "another_provider"])

        assert registry.get_provider_count() == 0
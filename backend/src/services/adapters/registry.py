"""
Provider registry for dynamic adapter registration and discovery.

Manages the registration, discovery, and instantiation of market data
provider adapters using a registry pattern with dependency injection support.
"""

from typing import Dict, List, Type, Optional, Any
import logging
from dataclasses import dataclass

from .base_adapter import MarketDataAdapter, AdapterResponse

logger = logging.getLogger(__name__)


@dataclass
class RegisteredProvider:
    """Information about a registered provider adapter."""

    adapter_class: Type[MarketDataAdapter]
    provider_name: str
    display_name: str
    description: str
    version: str
    is_enabled: bool = True


class ProviderRegistry:
    """
    Registry for managing market data provider adapters.

    Implements the registry pattern to allow dynamic registration and
    discovery of adapter implementations. Supports enabling/disabling
    providers and provides metadata for admin interfaces.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._providers: Dict[str, RegisteredProvider] = {}
        self._instances: Dict[str, MarketDataAdapter] = {}
        self.logger = logging.getLogger("adapter.registry")

    def register_provider(
        self,
        adapter_class: Type[MarketDataAdapter],
        provider_name: str,
        display_name: str,
        description: str = "",
        version: str = "1.0.0",
        is_enabled: bool = True
    ) -> None:
        """
        Register a provider adapter class.

        Args:
            adapter_class: The adapter class implementing MarketDataAdapter
            provider_name: Unique identifier for the provider
            display_name: Human-readable name for UI display
            description: Description of the provider
            version: Provider version
            is_enabled: Whether the provider is enabled by default
        """
        if not issubclass(adapter_class, MarketDataAdapter):
            raise ValueError(f"Adapter class must inherit from MarketDataAdapter")

        if provider_name in self._providers:
            self.logger.warning(f"Provider {provider_name} already registered, overwriting")

        self._providers[provider_name] = RegisteredProvider(
            adapter_class=adapter_class,
            provider_name=provider_name,
            display_name=display_name,
            description=description,
            version=version,
            is_enabled=is_enabled
        )

        self.logger.info(f"Registered provider: {provider_name} ({display_name} v{version})")

    def unregister_provider(self, provider_name: str) -> bool:
        """
        Unregister a provider adapter.

        Args:
            provider_name: Name of provider to unregister

        Returns:
            True if provider was unregistered, False if not found
        """
        if provider_name in self._providers:
            # Clean up any existing instance
            if provider_name in self._instances:
                asyncio.create_task(self._instances[provider_name].cleanup())
                del self._instances[provider_name]

            del self._providers[provider_name]
            self.logger.info(f"Unregistered provider: {provider_name}")
            return True

        return False

    def is_provider_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered."""
        return provider_name in self._providers

    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled."""
        provider = self._providers.get(provider_name)
        return provider.is_enabled if provider else False

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a registered provider."""
        if provider_name in self._providers:
            self._providers[provider_name].is_enabled = True
            self.logger.info(f"Enabled provider: {provider_name}")
            return True
        return False

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a registered provider."""
        if provider_name in self._providers:
            self._providers[provider_name].is_enabled = False

            # Clean up any existing instance
            if provider_name in self._instances:
                import asyncio
                asyncio.create_task(self._instances[provider_name].cleanup())
                del self._instances[provider_name]

            self.logger.info(f"Disabled provider: {provider_name}")
            return True
        return False

    def get_provider_info(self, provider_name: str) -> Optional[RegisteredProvider]:
        """Get information about a registered provider."""
        return self._providers.get(provider_name)

    def list_providers(self, enabled_only: bool = False) -> List[RegisteredProvider]:
        """
        List all registered providers.

        Args:
            enabled_only: If True, only return enabled providers

        Returns:
            List of registered provider information
        """
        providers = list(self._providers.values())

        if enabled_only:
            providers = [p for p in providers if p.is_enabled]

        return sorted(providers, key=lambda p: p.display_name)

    def get_available_provider_names(self, enabled_only: bool = True) -> List[str]:
        """
        Get list of available provider names.

        Args:
            enabled_only: If True, only return enabled providers

        Returns:
            List of provider names
        """
        providers = self.list_providers(enabled_only=enabled_only)
        return [p.provider_name for p in providers]

    async def create_provider_instance(
        self,
        provider_name: str,
        config: Dict[str, Any],
        force_new: bool = False
    ) -> Optional[MarketDataAdapter]:
        """
        Create an instance of a provider adapter.

        Args:
            provider_name: Name of the provider to instantiate
            config: Configuration for the provider
            force_new: If True, create new instance even if one exists

        Returns:
            Adapter instance or None if provider not found/disabled
        """
        provider_info = self._providers.get(provider_name)

        if not provider_info:
            self.logger.error(f"Provider not registered: {provider_name}")
            return None

        if not provider_info.is_enabled:
            self.logger.error(f"Provider not enabled: {provider_name}")
            return None

        # Return existing instance if available and not forcing new
        if not force_new and provider_name in self._instances:
            return self._instances[provider_name]

        # Create new instance
        try:
            instance = provider_info.adapter_class(provider_name, config)

            # Initialize the adapter
            if await instance.initialize():
                self._instances[provider_name] = instance
                self.logger.info(f"Created provider instance: {provider_name}")
                return instance
            else:
                self.logger.error(f"Failed to initialize provider: {provider_name}")
                await instance.cleanup()
                return None

        except Exception as e:
            self.logger.error(f"Error creating provider instance {provider_name}: {e}")
            return None

    async def get_provider_instance(self, provider_name: str) -> Optional[MarketDataAdapter]:
        """
        Get existing provider instance.

        Args:
            provider_name: Name of the provider

        Returns:
            Existing adapter instance or None
        """
        return self._instances.get(provider_name)

    def get_provider_capabilities_summary(self) -> Dict[str, Any]:
        """
        Get summary of capabilities across all providers.

        Returns:
            Dict with aggregated capability information
        """
        summary = {
            "total_providers": len(self._providers),
            "enabled_providers": len([p for p in self._providers.values() if p.is_enabled]),
            "supports_real_time": [],
            "supports_historical": [],
            "supports_bulk_quotes": [],
            "free_providers": [],
            "paid_providers": []
        }

        for provider_name, provider_info in self._providers.items():
            if not provider_info.is_enabled:
                continue

            # We can't get capabilities without instantiating, so this is
            # a simplified version that would need to be enhanced
            summary["supports_real_time"].append(provider_name)
            summary["supports_historical"].append(provider_name)

        return summary

    async def cleanup_all_instances(self) -> None:
        """Clean up all provider instances."""
        for provider_name, instance in self._instances.items():
            try:
                await instance.cleanup()
                self.logger.info(f"Cleaned up provider instance: {provider_name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up provider {provider_name}: {e}")

        self._instances.clear()

    def validate_provider_config(self, provider_name: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration for a provider.

        Args:
            provider_name: Name of the provider
            config: Configuration to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        provider_info = self._providers.get(provider_name)
        if not provider_info:
            return [f"Provider '{provider_name}' not registered"]

        # Create temporary instance to get schema
        try:
            temp_instance = provider_info.adapter_class(provider_name, {})
            schema = temp_instance.get_configuration_schema()

            # Basic validation - in production this would use jsonschema
            errors = []
            required_fields = schema.get("required", [])
            properties = schema.get("properties", {})

            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")

            for field, value in config.items():
                if field in properties:
                    field_type = properties[field].get("type")
                    if field_type == "string" and not isinstance(value, str):
                        errors.append(f"Field '{field}' must be a string")
                    elif field_type == "number" and not isinstance(value, (int, float)):
                        errors.append(f"Field '{field}' must be a number")

            return errors

        except Exception as e:
            return [f"Error validating configuration: {str(e)}"]


# Global registry instance
_global_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    return _global_registry


def register_provider(*args, **kwargs) -> None:
    """Convenience function to register a provider with the global registry."""
    _global_registry.register_provider(*args, **kwargs)
"""
Configuration manager for market data provider adapters.

Provides centralized configuration management with dependency injection,
validation, encryption of sensitive data, and dynamic configuration updates.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from sqlalchemy.orm import Session
from dependency_injector import containers, providers
import json
from cryptography.fernet import Fernet
import os

from src.database import get_db
from src.models.provider_configuration import ProviderConfiguration
from src.models.adapter_registry import AdapterRegistry
from src.services.adapters.registry import get_provider_registry, ProviderRegistry
from src.services.adapters.base_adapter import MarketDataAdapter

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Centralized configuration manager for market data provider adapters.

    Handles configuration validation, encryption of sensitive data,
    and provides dependency injection for adapter instances.
    """

    def __init__(self, db_session: Session, encryption_key: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            db_session: Database session for configuration persistence
            encryption_key: Key for encrypting sensitive configuration data
        """
        self.db_session = db_session
        self.provider_registry = get_provider_registry()
        self.logger = logging.getLogger("config.manager")

        # Initialize encryption for sensitive data
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # In production, this should come from environment or key management
            self.encryption_key = os.environ.get("ADAPTER_ENCRYPTION_KEY", Fernet.generate_key())

        if isinstance(self.encryption_key, str):
            self.encryption_key = self.encryption_key.encode()

        self.cipher = Fernet(self.encryption_key)

        # Cache for active configurations
        self._config_cache: Dict[str, ProviderConfiguration] = {}
        self._adapter_cache: Dict[str, MarketDataAdapter] = {}

    def create_provider_configuration(
        self,
        provider_name: str,
        display_name: str,
        config_data: Dict[str, Any],
        created_by_user_id: str,
        is_active: bool = False
    ) -> ProviderConfiguration:
        """
        Create and validate a new provider configuration.

        Args:
            provider_name: Type of adapter (alpha_vantage, yahoo_finance, etc.)
            display_name: Human-readable name for admin UI
            config_data: Provider-specific configuration
            created_by_user_id: ID of admin user creating configuration
            is_active: Whether to activate immediately

        Returns:
            Created ProviderConfiguration instance

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If provider type is not supported
        """
        # Validate provider type exists
        if not self.provider_registry.is_provider_registered(provider_name):
            raise RuntimeError(f"Provider type '{provider_name}' is not registered")

        # Validate configuration against provider schema
        validation_errors = self.provider_registry.validate_provider_config(provider_name, config_data)
        if validation_errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(validation_errors)}")

        # Encrypt sensitive fields
        encrypted_config = self._encrypt_sensitive_fields(provider_name, config_data)

        # Create configuration record
        config = ProviderConfiguration(
            provider_name=provider_name,
            display_name=display_name,
            config_data=encrypted_config,
            is_active=is_active,
            created_by_user_id=created_by_user_id
        )

        self.db_session.add(config)
        self.db_session.commit()

        self.logger.info(f"Created configuration for {provider_name}: {display_name}")

        # Clear cache to force reload
        self._clear_cache()

        return config

    def update_provider_configuration(
        self,
        config_id: str,
        updates: Dict[str, Any]
    ) -> ProviderConfiguration:
        """
        Update an existing provider configuration.

        Args:
            config_id: UUID of configuration to update
            updates: Fields to update

        Returns:
            Updated ProviderConfiguration instance

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If configuration not found
        """
        config = self.db_session.query(ProviderConfiguration).filter(
            ProviderConfiguration.id == config_id
        ).first()

        if not config:
            raise RuntimeError(f"Configuration {config_id} not found")

        # Update allowed fields
        if "display_name" in updates:
            config.display_name = updates["display_name"]

        if "is_active" in updates:
            config.is_active = updates["is_active"]

        if "config_data" in updates:
            # Merge with existing config and validate
            current_config = self._decrypt_sensitive_fields(config.provider_name, config.config_data)
            updated_config = {**current_config, **updates["config_data"]}

            # Validate merged configuration
            validation_errors = self.provider_registry.validate_provider_config(
                config.provider_name, updated_config
            )
            if validation_errors:
                raise ValueError(f"Configuration validation failed: {'; '.join(validation_errors)}")

            # Encrypt and update
            config.config_data = self._encrypt_sensitive_fields(config.provider_name, updated_config)

        self.db_session.commit()

        self.logger.info(f"Updated configuration {config_id}")

        # Clear cache to force reload
        self._clear_cache()

        return config

    def get_provider_configuration(self, config_id: str) -> Optional[ProviderConfiguration]:
        """Get provider configuration by ID."""
        return self.db_session.query(ProviderConfiguration).filter(
            ProviderConfiguration.id == config_id
        ).first()

    def get_active_configurations(self) -> List[ProviderConfiguration]:
        """Get all active provider configurations."""
        return self.db_session.query(ProviderConfiguration).filter(
            ProviderConfiguration.is_active == True
        ).all()

    def get_configurations_by_provider(self, provider_name: str) -> List[ProviderConfiguration]:
        """Get all configurations for a specific provider type."""
        return self.db_session.query(ProviderConfiguration).filter(
            ProviderConfiguration.provider_name == provider_name
        ).all()

    async def get_adapter_instance(self, config_id: str) -> Optional[MarketDataAdapter]:
        """
        Get or create adapter instance for configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Initialized adapter instance or None if not found/invalid
        """
        # Check cache first
        if config_id in self._adapter_cache:
            return self._adapter_cache[config_id]

        config = self.get_provider_configuration(config_id)
        if not config or not config.is_active:
            return None

        # Decrypt configuration for adapter
        decrypted_config = self._decrypt_sensitive_fields(config.provider_name, config.config_data)

        # Create adapter instance
        adapter = await self.provider_registry.create_provider_instance(
            config.provider_name,
            decrypted_config
        )

        if adapter:
            # Cache the instance
            self._adapter_cache[config_id] = adapter
            self.logger.info(f"Created adapter instance for {config.provider_name}")

        return adapter

    def delete_provider_configuration(self, config_id: str) -> bool:
        """
        Delete a provider configuration.

        Args:
            config_id: Configuration ID to delete

        Returns:
            True if deleted, False if not found
        """
        config = self.get_provider_configuration(config_id)
        if not config:
            return False

        # Clean up any cached adapter instance
        if config_id in self._adapter_cache:
            adapter = self._adapter_cache[config_id]
            # Cleanup adapter resources asynchronously
            import asyncio
            asyncio.create_task(adapter.cleanup())
            del self._adapter_cache[config_id]

        # Soft delete - set inactive instead of hard delete to preserve metrics
        config.is_active = False
        self.db_session.commit()

        self.logger.info(f"Deleted configuration {config_id}")
        return True

    def validate_configuration(self, provider_name: str, config_data: Dict[str, Any]) -> List[str]:
        """
        Validate configuration without creating it.

        Args:
            provider_name: Provider type
            config_data: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.provider_registry.is_provider_registered(provider_name):
            return [f"Provider type '{provider_name}' is not registered"]

        return self.provider_registry.validate_provider_config(provider_name, config_data)

    def get_configuration_schema(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration schema for a provider type."""
        provider_info = self.provider_registry.get_provider_info(provider_name)
        if not provider_info:
            return None

        # Get schema from adapter class
        try:
            temp_adapter = provider_info.adapter_class(provider_name, {})
            return temp_adapter.get_configuration_schema()
        except Exception as e:
            self.logger.error(f"Error getting schema for {provider_name}: {e}")
            return None

    def get_example_configuration(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get example configuration for a provider type."""
        provider_info = self.provider_registry.get_provider_info(provider_name)
        if not provider_info:
            return None

        # Get example from adapter class
        try:
            temp_adapter = provider_info.adapter_class(provider_name, {})
            return temp_adapter.get_example_configuration()
        except Exception as e:
            self.logger.error(f"Error getting example config for {provider_name}: {e}")
            return None

    def _encrypt_sensitive_fields(self, provider_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in configuration data."""
        # Define sensitive fields that should be encrypted
        sensitive_fields = {"api_key", "secret_key", "password", "token", "credentials"}

        encrypted_config = config_data.copy()

        for field_name, field_value in config_data.items():
            if field_name.lower() in sensitive_fields and isinstance(field_value, str):
                # Encrypt the field value
                encrypted_value = self.cipher.encrypt(field_value.encode()).decode()
                encrypted_config[field_name] = f"encrypted:{encrypted_value}"

        return encrypted_config

    def _decrypt_sensitive_fields(self, provider_name: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in configuration data."""
        decrypted_config = config_data.copy()

        for field_name, field_value in config_data.items():
            if isinstance(field_value, str) and field_value.startswith("encrypted:"):
                # Decrypt the field value
                encrypted_value = field_value[10:]  # Remove "encrypted:" prefix
                try:
                    decrypted_value = self.cipher.decrypt(encrypted_value.encode()).decode()
                    decrypted_config[field_name] = decrypted_value
                except Exception as e:
                    self.logger.error(f"Error decrypting field {field_name}: {e}")
                    # Keep encrypted value if decryption fails
                    decrypted_config[field_name] = field_value

        return decrypted_config

    def _clear_cache(self):
        """Clear configuration and adapter caches."""
        self._config_cache.clear()
        # Don't clear adapter cache immediately - let them be cleaned up gracefully
        # self._adapter_cache.clear()

    async def cleanup(self):
        """Clean up all adapter instances and resources."""
        for adapter in self._adapter_cache.values():
            try:
                await adapter.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up adapter: {e}")

        self._adapter_cache.clear()
        self.logger.info("Configuration manager cleanup complete")


class AdapterContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for adapter configuration.

    Provides configured adapter instances through dependency injection.
    """

    # Configuration
    config = providers.Configuration()

    # Database session
    db_session = providers.Singleton(get_db)

    # Configuration manager
    config_manager = providers.Singleton(
        ConfigurationManager,
        db_session=db_session,
        encryption_key=config.encryption_key
    )

    # Provider registry
    provider_registry = providers.Singleton(get_provider_registry)


# Global container instance
container = AdapterContainer()


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    return container.config_manager()
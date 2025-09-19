"""
Database model for adapter registry metadata.

Stores information about available market data provider adapters
including their capabilities, supported operations, and configuration schemas.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID

from src.database import Base
from src.utils.datetime_utils import now


class AdapterRegistry(Base):
    """Model for adapter registry containing available provider types."""

    __tablename__ = "adapter_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adapter_name = Column(String(50), unique=True, nullable=False)  # Unique identifier for adapter type
    display_name = Column(String(100), nullable=False)  # Human-readable name
    description = Column(String(500), nullable=True)  # Adapter description
    version = Column(String(20), nullable=False)  # Adapter version
    is_enabled = Column(Boolean, default=True, nullable=False)  # Enable/disable adapter type
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # Adapter capabilities
    supports_real_time = Column(Boolean, default=False, nullable=False)
    supports_historical = Column(Boolean, default=True, nullable=False)
    supports_bulk_quotes = Column(Boolean, default=False, nullable=False)
    max_symbols_per_request = Column(Integer, default=1, nullable=False)

    # Rate limiting info
    rate_limit_per_minute = Column(Integer, nullable=True)  # Calls per minute limit
    rate_limit_per_day = Column(Integer, nullable=True)  # Calls per day limit
    rate_limit_per_month = Column(Integer, nullable=True)  # Calls per month limit

    # Cost information
    cost_per_call_usd = Column(String(20), nullable=True)  # Cost as string (e.g., "0.0001" or "free")
    cost_model = Column(String(50), nullable=True)  # e.g., "per_call", "subscription", "freemium"

    # Configuration schema
    config_schema = Column(JSON, nullable=False)  # JSON Schema for configuration validation
    config_example = Column(JSON, nullable=True)  # Example configuration

    # Provider metadata
    provider_url = Column(String(200), nullable=True)  # Provider's official URL
    documentation_url = Column(String(200), nullable=True)  # API documentation URL
    signup_url = Column(String(200), nullable=True)  # Registration URL

    def __repr__(self) -> str:
        return f"<AdapterRegistry(name={self.adapter_name}, version={self.version}, enabled={self.is_enabled})>"

    @property
    def is_free_tier(self) -> bool:
        """Check if adapter offers free tier."""
        return self.cost_per_call_usd == "free" or self.cost_model == "freemium"

    @property
    def supports_batch_operations(self) -> bool:
        """Check if adapter supports batch operations."""
        return self.max_symbols_per_request > 1

    def get_rate_limit_summary(self) -> dict:
        """Get summary of rate limits."""
        return {
            "per_minute": self.rate_limit_per_minute,
            "per_day": self.rate_limit_per_day,
            "per_month": self.rate_limit_per_month
        }

    def validate_config(self, config_data: dict) -> bool:
        """Validate configuration against schema (placeholder)."""
        # TODO: Implement JSON Schema validation in service layer
        required_fields = self.config_schema.get("required", [])
        return all(field in config_data for field in required_fields)

    def get_capabilities_summary(self) -> dict:
        """Get summary of adapter capabilities."""
        return {
            "real_time": self.supports_real_time,
            "historical": self.supports_historical,
            "bulk_quotes": self.supports_bulk_quotes,
            "max_symbols": self.max_symbols_per_request,
            "batch_support": self.supports_batch_operations
        }

    @classmethod
    def create_adapter_entry(
        cls,
        adapter_name: str,
        display_name: str,
        version: str,
        config_schema: dict,
        **kwargs
    ) -> "AdapterRegistry":
        """Create a new adapter registry entry."""
        return cls(
            adapter_name=adapter_name,
            display_name=display_name,
            version=version,
            config_schema=config_schema,
            description=kwargs.get("description"),
            supports_real_time=kwargs.get("supports_real_time", False),
            supports_historical=kwargs.get("supports_historical", True),
            supports_bulk_quotes=kwargs.get("supports_bulk_quotes", False),
            max_symbols_per_request=kwargs.get("max_symbols_per_request", 1),
            rate_limit_per_minute=kwargs.get("rate_limit_per_minute"),
            rate_limit_per_day=kwargs.get("rate_limit_per_day"),
            rate_limit_per_month=kwargs.get("rate_limit_per_month"),
            cost_per_call_usd=kwargs.get("cost_per_call_usd"),
            cost_model=kwargs.get("cost_model"),
            config_example=kwargs.get("config_example"),
            provider_url=kwargs.get("provider_url"),
            documentation_url=kwargs.get("documentation_url"),
            signup_url=kwargs.get("signup_url")
        )
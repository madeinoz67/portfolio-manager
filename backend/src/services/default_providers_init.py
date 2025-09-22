"""
Default provider initialization service.

Automatically creates default market data providers during application startup.
This ensures YFinance and Alpha Vantage providers are always available by default.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
from src.models.provider_configuration import ProviderConfiguration
from src.services.adapters.registry import get_provider_registry

logger = logging.getLogger(__name__)


def create_default_providers() -> None:
    """
    Create default market data providers during application startup.

    This function ensures that YFinance and Alpha Vantage providers are
    automatically available in the system with sensible default configurations.
    """
    db = next(get_db())
    try:
        _create_yfinance_provider(db)
        _create_alpha_vantage_provider(db)
        db.commit()
        logger.info("Default providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize default providers: {e}")
        db.rollback()
    finally:
        db.close()


def _create_yfinance_provider(db: Session) -> None:
    """Create YFinance provider with default configuration."""
    provider_name = "yfinance_default"

    # Check if provider already exists
    existing = db.query(ProviderConfiguration).filter(
        ProviderConfiguration.provider_name == provider_name
    ).first()

    if existing:
        logger.info(f"YFinance provider '{provider_name}' already exists")
        return

    # Get registry to validate adapter exists
    registry = get_provider_registry()
    if "yfinance" not in registry.get_available_provider_names():
        logger.warning("YFinance adapter not found in registry, skipping provider creation")
        return

    # Create system user for default providers if it doesn't exist
    from src.models.user import User
    system_user = db.query(User).filter(User.email == "system@portfolio-manager.local").first()
    if not system_user:
        # Create a system user for default providers
        import uuid
        from src.core.auth import get_password_hash
        system_user = User(
            id=uuid.uuid4(),
            email="system@portfolio-manager.local",
            password_hash=get_password_hash("system-password-not-used"),
            first_name="System",
            last_name="Default",
            role="admin",
            is_active=True
        )
        db.add(system_user)
        db.flush()

    # Create default YFinance provider
    yfinance_config = {
        "adapter_type": "yfinance",
        "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
        "timeout": 30,
        "rate_limit_per_minute": 100,
        "rate_limit_per_day": 10000,
        "requires_api_key": False
    }

    provider = ProviderConfiguration(
        provider_name=provider_name,
        display_name="Yahoo Finance (Default)",
        is_active=True,  # YFinance enabled by default
        config_data=yfinance_config,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by_user_id=system_user.id
    )

    try:
        db.add(provider)
        db.flush()  # Flush to catch any constraint violations early
        logger.info(f"Created default YFinance provider: {provider_name}")
    except IntegrityError as e:
        logger.warning(f"YFinance provider creation skipped (already exists): {e}")
        db.rollback()


def _create_alpha_vantage_provider(db: Session) -> None:
    """Create Alpha Vantage provider with default configuration (disabled by default)."""
    provider_name = "alpha_vantage_default"

    # Check if provider already exists
    existing = db.query(ProviderConfiguration).filter(
        ProviderConfiguration.provider_name == provider_name
    ).first()

    if existing:
        logger.info(f"Alpha Vantage provider '{provider_name}' already exists")
        return

    # Get registry to validate adapter exists
    registry = get_provider_registry()
    if "alpha_vantage" not in registry.get_available_provider_names():
        logger.warning("Alpha Vantage adapter not found in registry, skipping provider creation")
        return

    # Get system user (should already exist from YFinance creation)
    from src.models.user import User
    system_user = db.query(User).filter(User.email == "system@portfolio-manager.local").first()
    if not system_user:
        logger.error("System user not found, cannot create Alpha Vantage provider")
        return

    # Create default Alpha Vantage provider (disabled by default - requires API key)
    alpha_vantage_config = {
        "adapter_type": "alpha_vantage",
        "api_key": "",  # Empty by default - admin must configure
        "base_url": "https://www.alphavantage.co/query",
        "timeout": 30,
        "rate_limit_per_minute": 5,  # Conservative default for free tier
        "rate_limit_per_day": 500,    # Free tier limit
        "requires_api_key": True
    }

    provider = ProviderConfiguration(
        provider_name=provider_name,
        display_name="Alpha Vantage (Default)",
        is_active=False,  # Disabled by default until API key is configured
        config_data=alpha_vantage_config,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by_user_id=system_user.id
    )

    try:
        db.add(provider)
        db.flush()  # Flush to catch any constraint violations early
        logger.info(f"Created default Alpha Vantage provider: {provider_name} (disabled)")
    except IntegrityError as e:
        logger.warning(f"Alpha Vantage provider creation skipped (already exists): {e}")
        db.rollback()


def get_default_providers_summary() -> dict:
    """
    Get summary of default providers status.

    Returns:
        Dictionary with information about default providers
    """
    db = next(get_db())
    try:
        yfinance = db.query(ProviderConfiguration).filter(
            ProviderConfiguration.provider_name == "yfinance_default"
        ).first()

        alpha_vantage = db.query(ProviderConfiguration).filter(
            ProviderConfiguration.provider_name == "alpha_vantage_default"
        ).first()

        return {
            "yfinance_default": {
                "exists": yfinance is not None,
                "enabled": yfinance.is_enabled if yfinance else False,
                "created_at": yfinance.created_at.isoformat() if yfinance else None
            },
            "alpha_vantage_default": {
                "exists": alpha_vantage is not None,
                "enabled": alpha_vantage.is_enabled if alpha_vantage else False,
                "created_at": alpha_vantage.created_at.isoformat() if alpha_vantage else None
            }
        }
    finally:
        db.close()
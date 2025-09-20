"""
Database configuration and session management.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# SQLite database URL
DATABASE_URL = "sqlite:///./portfolio.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Only for SQLite
    echo=True,  # Enable SQL logging in development
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models  
class Base(DeclarativeBase):
    # Allow legacy annotations temporarily
    __allow_unmapped__ = True


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import adapter models to ensure they're registered with SQLAlchemy
# This ensures the models are available for migrations and queries
def import_adapter_models():
    """Import all adapter-related models to register them with SQLAlchemy."""
    try:
        # Import provider configuration and management models
        from src.models.provider_configuration import ProviderConfiguration
        from src.models.provider_metrics import ProviderMetrics
        from src.models.cost_tracking_record import CostTrackingRecord
        from src.models.adapter_registry import AdapterRegistry
        from src.models.adapter_health_check import AdapterHealthCheck

        # Import market data provider model if it exists
        try:
            from src.models.market_data_provider import MarketDataProvider
        except ImportError:
            pass  # Model might not exist yet

    except ImportError as e:
        # Models might not be fully implemented yet
        pass


# Import models on module load
import_adapter_models()

"""
Configuration management for the Portfolio Manager application.

Handles environment-specific settings for development, testing, and production.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Portfolio Manager API"
    app_version: str = "0.2.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    reload: bool = False

    # Security
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Database
    database_url: str = "sqlite:///./portfolio_manager.db"
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Market Data Providers - yfinance only for ASX support
    alpha_vantage_api_key: Optional[str] = None
    alpha_vantage_enabled: bool = False  # Disabled - no ASX support
    alpha_vantage_base_url: str = "https://www.alphavantage.co"
    alpha_vantage_rate_limit_per_minute: int = 5
    alpha_vantage_rate_limit_per_day: int = 500

    yfinance_enabled: bool = True  # Primary provider for ASX data
    yfinance_rate_limit_per_minute: int = 60
    yfinance_rate_limit_per_day: int = 2000
    yfinance_priority: int = 1  # Highest priority

    # Cache Settings
    redis_url: Optional[str] = None
    cache_ttl_minutes: int = 20
    price_cache_ttl_minutes: int = 15

    # Market Data Update Settings
    default_poll_interval_minutes: int = 15
    max_symbols_per_request: int = 50
    max_sse_connections_per_user: int = 5
    sse_heartbeat_interval_seconds: int = 30

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 200
    refresh_rate_limit_seconds: int = 60

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004"
    ]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or plain
    log_file: Optional[str] = None

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval_seconds: int = 30

    # Error Handling
    sentry_dsn: Optional[str] = None
    enable_error_reporting: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "PM_"
        case_sensitive = False

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        if v.startswith('sqlite://') and not v.startswith('sqlite:///'):
            # Convert relative sqlite paths to absolute
            if not v.startswith('sqlite:///'):
                v = v.replace('sqlite://', 'sqlite:///./')
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return os.getenv('ENVIRONMENT', '').lower() == 'production'

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'

    @property
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return os.getenv('ENVIRONMENT', '').lower() == 'testing'


class DatabaseSettings(BaseSettings):
    """Database-specific settings for different environments."""

    # PostgreSQL Production Settings
    postgres_user: str = "portfolio_user"
    postgres_password: str = ""
    postgres_db: str = "portfolio_manager"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Connection Pool Settings
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour

    class Config:
        env_prefix = "PM_DB_"

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class RedisSettings(BaseSettings):
    """Redis cache settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False

    # Connection Pool
    max_connections: int = 50
    retry_on_timeout: bool = True
    socket_timeout: int = 5

    class Config:
        env_prefix = "PM_REDIS_"

    @property
    def url(self) -> str:
        """Generate Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


# Global settings instance
settings = Settings()
db_settings = DatabaseSettings()
redis_settings = RedisSettings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def get_database_url() -> str:
    """Get database URL based on environment."""
    if settings.is_production and db_settings.postgres_password:
        return db_settings.postgres_url
    return settings.database_url


def get_cache_url() -> Optional[str]:
    """Get cache URL if Redis is configured."""
    if redis_settings.password or settings.redis_url:
        return settings.redis_url or redis_settings.url
    return None


# Environment-specific overrides
if settings.is_production:
    # Production overrides
    settings.debug = False
    settings.reload = False
    settings.database_echo = False
    settings.log_level = "WARNING"

elif settings.is_testing:
    # Testing overrides
    settings.database_url = "sqlite:///:memory:"
    settings.cache_ttl_minutes = 1
    settings.jwt_expire_minutes = 5
    settings.rate_limit_requests_per_minute = 1000

elif settings.is_development:
    # Development overrides
    settings.debug = True
    settings.reload = True
    settings.database_echo = True
    settings.log_level = "DEBUG"
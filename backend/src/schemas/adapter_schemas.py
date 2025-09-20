"""
Pydantic schemas for adapter configuration management.

Defines request/response schemas for adapter CRUD operations,
configuration validation, and provider management.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from enum import Enum


class ProviderType(str, Enum):
    """Supported market data provider types."""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"
    POLYGON = "polygon"
    FINNHUB = "finnhub"


class AdapterStatus(str, Enum):
    """Adapter configuration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"


class AdapterCapability(BaseModel):
    """Provider capability definition."""
    supports_bulk_quotes: bool = Field(default=False, description="Supports bulk quote requests")
    supports_historical_data: bool = Field(default=False, description="Supports historical price data")
    supports_real_time: bool = Field(default=False, description="Supports real-time data")
    max_symbols_per_request: Optional[int] = Field(None, description="Maximum symbols per bulk request")
    rate_limit_per_minute: Optional[int] = Field(None, description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(None, description="Rate limit per day")
    requires_api_key: bool = Field(default=True, description="Requires API key authentication")
    supported_data_types: List[str] = Field(default_factory=list, description="Supported data types")


class AdapterConfigurationBase(BaseModel):
    """Base adapter configuration schema."""
    provider_name: ProviderType = Field(..., description="Type of market data provider")
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable name")
    description: Optional[str] = Field(None, max_length=500, description="Configuration description")
    is_active: bool = Field(default=False, description="Whether adapter is active")


class AdapterConfigurationCreate(AdapterConfigurationBase):
    """Schema for creating new adapter configurations."""
    config_data: Dict[str, Any] = Field(..., description="Provider-specific configuration")

    @validator('config_data')
    def validate_config_data(cls, v):
        """Validate configuration data structure."""
        if not isinstance(v, dict):
            raise ValueError('config_data must be a dictionary')

        # Basic validation - specific validation happens in ConfigurationManager
        required_fields = ['api_key'] if v.get('requires_api_key', True) else []
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field: {field}')

        return v


class AdapterConfigurationUpdate(BaseModel):
    """Schema for updating adapter configurations."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config_data: Optional[Dict[str, Any]] = Field(None, description="Configuration updates")
    is_active: Optional[bool] = Field(None, description="Active status")

    model_config = ConfigDict(extra='forbid')


class AdapterConfigurationResponse(AdapterConfigurationBase):
    """Schema for adapter configuration responses."""
    id: str = Field(..., description="Unique configuration identifier")
    config_data: Dict[str, Any] = Field(..., description="Provider configuration (sensitive fields masked)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by_user_id: str = Field(..., description="Creator user ID")
    status: AdapterStatus = Field(default=AdapterStatus.INACTIVE, description="Current status")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    error_message: Optional[str] = Field(None, description="Last error message if any")

    model_config = ConfigDict(from_attributes=True)


class AdapterListFilter(BaseModel):
    """Schema for adapter listing filters."""
    provider_name: Optional[ProviderType] = Field(None, description="Filter by provider type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    status: Optional[AdapterStatus] = Field(None, description="Filter by status")
    created_by_user_id: Optional[str] = Field(None, description="Filter by creator")
    search: Optional[str] = Field(None, description="Search in display name and description")


class AdapterListSort(str, Enum):
    """Sorting options for adapter lists."""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DISPLAY_NAME = "display_name"
    PROVIDER_NAME = "provider_name"
    STATUS = "status"
    PRIORITY = "priority"


class AdapterListResponse(BaseModel):
    """Schema for paginated adapter listing."""
    items: List[AdapterConfigurationResponse] = Field(..., description="Adapter configurations")
    total: int = Field(..., ge=0, description="Total number of configurations")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class ProviderRegistryEntry(BaseModel):
    """Schema for provider registry entries."""
    name: ProviderType = Field(..., description="Provider type identifier")
    display_name: str = Field(..., description="Human-readable provider name")
    description: str = Field(..., description="Provider description")
    capabilities: AdapterCapability = Field(..., description="Provider capabilities")
    is_available: bool = Field(..., description="Whether provider is available")
    configuration_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for configuration")
    example_configuration: Optional[Dict[str, Any]] = Field(None, description="Example configuration")
    documentation_url: Optional[str] = Field(None, description="Provider documentation URL")


class ProviderRegistryResponse(BaseModel):
    """Schema for provider registry listing."""
    available_adapters: List[ProviderRegistryEntry] = Field(..., description="Available provider types")
    total_adapters: int = Field(..., ge=0, description="Total number of available adapters")


class AdapterHealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


class AdapterHealthResponse(BaseModel):
    """Schema for adapter health status."""
    adapter_id: str = Field(..., description="Adapter configuration ID")
    provider_name: ProviderType = Field(..., description="Provider type")
    status: AdapterHealthStatus = Field(..., description="Current health status")
    last_check: datetime = Field(..., description="Last health check timestamp")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate (0.0 to 1.0)")
    avg_latency_ms: float = Field(..., ge=0.0, description="Average latency in milliseconds")
    error_count: int = Field(..., ge=0, description="Recent error count")
    circuit_breaker_state: str = Field(..., description="Circuit breaker state")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_success: Optional[datetime] = Field(None, description="Last successful request timestamp")


class AdapterValidationRequest(BaseModel):
    """Schema for configuration validation requests."""
    provider_name: ProviderType = Field(..., description="Provider type to validate")
    config_data: Dict[str, Any] = Field(..., description="Configuration to validate")


class AdapterValidationResponse(BaseModel):
    """Schema for configuration validation results."""
    is_valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Configuration improvement suggestions")


class AdapterTestRequest(BaseModel):
    """Schema for adapter test requests."""
    test_symbol: str = Field(default="AAPL", description="Symbol to test with")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Test timeout")


class AdapterTestResponse(BaseModel):
    """Schema for adapter test results."""
    adapter_id: str = Field(..., description="Tested adapter ID")
    success: bool = Field(..., description="Whether test was successful")
    response_time_ms: float = Field(..., ge=0.0, description="Response time in milliseconds")
    test_symbol: str = Field(..., description="Symbol used for testing")
    price_data: Optional[Dict[str, Any]] = Field(None, description="Retrieved price data")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    timestamp: datetime = Field(..., description="Test execution timestamp")


class AdapterBulkAction(str, Enum):
    """Bulk action types."""
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    DELETE = "delete"
    TEST = "test"
    REFRESH_HEALTH = "refresh_health"


class AdapterBulkRequest(BaseModel):
    """Schema for bulk adapter operations."""
    adapter_ids: List[str] = Field(..., min_items=1, description="List of adapter IDs")
    action: AdapterBulkAction = Field(..., description="Action to perform")
    force: bool = Field(default=False, description="Force action even if risky")


class AdapterBulkResultItem(BaseModel):
    """Schema for individual bulk operation results."""
    adapter_id: str = Field(..., description="Adapter ID")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    error_code: Optional[str] = Field(None, description="Error code if failed")


class AdapterBulkResponse(BaseModel):
    """Schema for bulk operation results."""
    action: AdapterBulkAction = Field(..., description="Performed action")
    total_requested: int = Field(..., ge=0, description="Total adapters requested")
    successful: int = Field(..., ge=0, description="Successfully processed adapters")
    failed: int = Field(..., ge=0, description="Failed adapter operations")
    results: List[AdapterBulkResultItem] = Field(..., description="Individual operation results")
    timestamp: datetime = Field(..., description="Operation timestamp")
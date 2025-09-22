"""
Admin API endpoints for market data adapter management.

Provides CRUD operations and monitoring for provider configurations,
including health checks, metrics, and registry management.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.database import get_db
from src.core.dependencies import get_current_admin_user
from src.models.user import User
from src.models.provider_configuration import ProviderConfiguration
from src.services.config_manager import ConfigurationManager, get_config_manager
from src.services.provider_manager import get_provider_manager, ProviderManager
from src.services.adapters.registry import get_provider_registry, ProviderRegistry
from src.services.adapter_metrics_service import AdapterMetricsService
from src.schemas.metrics_schemas import AdapterMetricsResponse
from src.schemas.adapter_schemas import AdapterHealthResponse, ProviderType, AdapterHealthStatus

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(
    prefix="/api/v1/admin/adapters",
    tags=["admin", "adapters"],
    dependencies=[Depends(security)]
)


# Request/Response Schemas
class AdapterConfigurationRequest(BaseModel):
    """Request schema for creating/updating adapter configurations."""
    provider_name: str = Field(..., description="Type of adapter (alpha_vantage, yahoo_finance, etc.)")
    display_name: str = Field(..., description="Human-readable name for admin UI")
    config_data: Dict[str, Any] = Field(..., description="Provider-specific configuration")
    is_active: bool = Field(default=False, description="Whether to activate immediately")


class AdapterConfigurationUpdate(BaseModel):
    """Request schema for partial adapter configuration updates."""
    display_name: Optional[str] = Field(None, description="Human-readable name for admin UI")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Provider-specific configuration")
    is_active: Optional[bool] = Field(None, description="Whether adapter is active")


class AdapterConfigurationResponse(BaseModel):
    """Response schema for adapter configurations."""
    id: str
    provider_name: str
    display_name: str
    config_data: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str

    class Config:
        from_attributes = True


class AdapterListResponse(BaseModel):
    """Response schema for adapter listing."""
    items: List[AdapterConfigurationResponse]
    total: int
    page: int
    page_size: int





class ProviderRegistryResponse(BaseModel):
    """Response schema for provider registry."""
    available_adapters: List[Dict[str, Any]]
    total_adapters: int


# T031: GET /api/v1/admin/adapters
@router.get("", response_model=AdapterListResponse)
async def list_adapters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    provider_name: Optional[str] = Query(None, description="Filter by provider type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort: Optional[str] = Query("created_at", description="Sort field"),
    order: Optional[str] = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    include_cost_summary: Optional[bool] = Query(False, description="Include cost summary"),
    include_cost_comparison: Optional[bool] = Query(False, description="Include cost comparison"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all adapter configurations with filtering and pagination.

    Supports filtering by provider type and active status,
    with pagination and sorting capabilities.
    """
    try:
        # Create config manager instance with the database session
        config_manager = ConfigurationManager(db)

        # Get ALL configurations (both active and inactive)
        if provider_name:
            configs = config_manager.get_configurations_by_provider(provider_name)
        else:
            # Get ALL provider configurations, not just active ones
            configs = db.query(ProviderConfiguration).all()

        # Apply active status filter if specified
        if is_active is not None:
            configs = [c for c in configs if c.is_active == is_active]

        # Sort configurations
        reverse_order = order == "desc"
        if sort == "created_at":
            configs.sort(key=lambda x: x.created_at, reverse=reverse_order)
        elif sort == "display_name":
            configs.sort(key=lambda x: x.display_name, reverse=reverse_order)
        elif sort == "provider_name":
            configs.sort(key=lambda x: x.provider_name, reverse=reverse_order)
        elif sort == "priority":
            configs.sort(key=lambda x: x.config_data.get("priority", 999), reverse=reverse_order)

        # Apply pagination
        total = len(configs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_configs = configs[start_idx:end_idx]

        # Convert to response format
        items = []
        for config in paginated_configs:
            response_item = AdapterConfigurationResponse(
                id=str(config.id),
                provider_name=config.provider_name,
                display_name=config.display_name,
                config_data=config.config_data,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at,
                created_by_user_id=str(config.created_by_user_id)
            )

            # Add cost/health information if requested
            if include_cost_summary or include_cost_comparison:
                # In a real implementation, would add cost data
                pass

            items.append(response_item)

        return AdapterListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing adapters: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T032: POST /api/v1/admin/adapters
@router.post("", response_model=AdapterConfigurationResponse, status_code=201)
async def create_adapter(
    request: AdapterConfigurationRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new adapter configuration.

    Validates the configuration against the provider schema
    and stores it with encrypted sensitive fields.
    """
    try:
        # Create config manager instance with the database session
        config_manager = ConfigurationManager(db)

        # Validate configuration before creating
        validation_errors = config_manager.validate_configuration(
            request.provider_name,
            request.config_data
        )

        if validation_errors:
            raise HTTPException(
                status_code=422,
                detail=f"Configuration validation failed: {'; '.join(validation_errors)}"
            )

        # Create the configuration
        config = config_manager.create_provider_configuration(
            provider_name=request.provider_name,
            display_name=request.display_name,
            config_data=request.config_data,
            created_by_user_id=str(current_admin.id),
            is_active=request.is_active
        )

        logger.info(f"Admin {current_admin.id} created adapter {config.id}")

        return AdapterConfigurationResponse(
            id=str(config.id),
            provider_name=config.provider_name,
            display_name=config.display_name,
            config_data=config.config_data,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by_user_id=str(config.created_by_user_id)
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating adapter: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T038: GET /api/v1/admin/adapters/registry
@router.get("/registry", response_model=ProviderRegistryResponse)
async def get_provider_registry_endpoint(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get information about all available adapter types.

    Returns registry of supported providers with their capabilities
    and configuration schemas.
    """
    def ensure_serializable(obj):
        """Recursively ensure all objects are JSON-serializable."""
        import json
        if hasattr(obj, '__dict__'):
            # Convert objects to their dict representation
            return {key: ensure_serializable(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {key: ensure_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ensure_serializable(item) for item in obj]
        else:
            # Convert to string for safety
            return str(obj) if obj is not None else None

    try:
        # Get provider registry instance
        provider_registry = get_provider_registry()

        # Get all registered providers
        available_providers = []

        for provider_info in provider_registry.list_providers():
            # provider_info is already a RegisteredProvider object

            if provider_info:
                # Get capabilities from adapter class
                try:
                    temp_adapter = provider_info.adapter_class(provider_info.provider_name, {})
                    # Ensure all values are JSON-serializable
                    supported_data_types = getattr(temp_adapter.capabilities, 'supported_data_types', [])
                    # Convert any objects to strings
                    if isinstance(supported_data_types, (list, tuple)):
                        supported_data_types = [str(item) for item in supported_data_types]
                    else:
                        supported_data_types = []

                    capabilities = {
                        "supports_bulk_quotes": bool(getattr(temp_adapter.capabilities, 'supports_bulk_quotes', False)),
                        "rate_limit_per_minute": getattr(temp_adapter.capabilities, 'rate_limit_per_minute', None),
                        "supported_data_types": supported_data_types,
                        "requires_api_key": bool(getattr(temp_adapter.capabilities, 'requires_api_key', True))
                    }
                except Exception:
                    capabilities = {}

                provider_data = {
                    "name": str(provider_info.provider_name),
                    "display_name": str(provider_info.display_name),
                    "description": str(provider_info.description),
                    "capabilities": capabilities,
                    "is_available": True
                }

                # Add configuration schema if available
                try:
                    temp_adapter = provider_info.adapter_class(provider_info.provider_name, {})
                    schema = temp_adapter.get_configuration_schema()
                    if schema:
                        # Ensure schema is JSON-serializable
                        provider_data["configuration_schema"] = ensure_serializable(schema)

                    example = temp_adapter.get_example_configuration()
                    if example:
                        # Ensure example is JSON-serializable
                        provider_data["example_configuration"] = ensure_serializable(example)

                except Exception:
                    pass

                # Ensure the entire provider_data is serializable
                provider_data = ensure_serializable(provider_data)
                available_providers.append(provider_data)

        # Final serialization check on the entire response
        response_data = {
            "available_adapters": ensure_serializable(available_providers),
            "total_adapters": len(available_providers)
        }

        # Return as plain JSON to avoid Pydantic serialization issues
        from fastapi.responses import JSONResponse
        return JSONResponse(content=response_data)

    except Exception as e:
        import traceback
        logger.error(f"Error getting provider registry: {e}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T033: GET /api/v1/admin/adapters/{id}
@router.get("/{adapter_id}", response_model=AdapterConfigurationResponse)
async def get_adapter(
    adapter_id: UUID = Path(..., description="Adapter configuration ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific adapter configuration by ID.

    Returns the full configuration including encrypted fields
    (masked for security).
    """
    try:
        # Create config manager instance with the database session
        config_manager = ConfigurationManager(db)

        config = config_manager.get_provider_configuration(adapter_id)

        if not config:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        return AdapterConfigurationResponse(
            id=str(config.id),
            provider_name=config.provider_name,
            display_name=config.display_name,
            config_data=config.config_data,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by_user_id=str(config.created_by_user_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T034: PUT /api/v1/admin/adapters/{id}
@router.put("/{adapter_id}", response_model=AdapterConfigurationResponse)
async def update_adapter(
    adapter_id: UUID = Path(..., description="Adapter configuration ID"),
    request: AdapterConfigurationUpdate = ...,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing adapter configuration.

    Supports partial updates and validates any configuration changes.
    """
    try:
        # Create config manager instance with the database session
        config_manager = ConfigurationManager(db)

        # Check if configuration exists
        existing_config = config_manager.get_provider_configuration(adapter_id)
        if not existing_config:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        # Prepare update data
        updates = {}
        if request.display_name is not None:
            updates["display_name"] = request.display_name
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.config_data is not None:
            updates["config_data"] = request.config_data

        # Update the configuration
        updated_config = config_manager.update_provider_configuration(
            str(adapter_id),
            updates
        )

        logger.info(f"Admin {current_admin.id} updated adapter {adapter_id}")

        return AdapterConfigurationResponse(
            id=str(updated_config.id),
            provider_name=updated_config.provider_name,
            display_name=updated_config.display_name,
            config_data=updated_config.config_data,
            is_active=updated_config.is_active,
            created_at=updated_config.created_at,
            updated_at=updated_config.updated_at,
            created_by_user_id=str(updated_config.created_by_user_id)
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T035: DELETE /api/v1/admin/adapters/{id}
@router.delete("/{adapter_id}", status_code=204)
async def delete_adapter(
    adapter_id: UUID = Path(..., description="Adapter configuration ID"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete an adapter configuration.

    Performs soft delete (sets inactive) to preserve metrics history.
    """
    try:
        # Create config manager instance with the database session
        config_manager = ConfigurationManager(db)

        success = config_manager.delete_provider_configuration(str(adapter_id))

        if not success:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        logger.info(f"Admin {current_admin.id} deleted adapter {adapter_id}")

        # Return 204 No Content on successful deletion
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T036: GET /api/v1/admin/adapters/{id}/metrics
@router.get("/{adapter_id}/metrics")
async def get_adapter_metrics(
    adapter_id: UUID = Path(..., description="Adapter configuration ID"),
    time_range: str = Query("24h", description="Time range for metrics (1h, 24h, 7d, 30d)"),
    include_cost_data: Optional[bool] = Query(False, description="Include cost information"),
    include_projections: Optional[bool] = Query(False, description="Include cost projections"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time metrics for a specific adapter using the adapter-based metrics system.

    This endpoint uses the new adapter architecture where each adapter is responsible
    for collecting and providing its own metrics.
    """
    try:
        # Use the new adapter metrics service
        metrics_service = AdapterMetricsService(db)

        # Get comprehensive adapter metrics (pass UUID object directly)
        adapter_metrics = await metrics_service.get_adapter_metrics(adapter_id, time_range)

        if not adapter_metrics:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        # Add additional cost data if requested
        if include_cost_data:
            total_requests = adapter_metrics.get("total_requests", 0)
            total_cost = adapter_metrics.get("total_cost", 0.0)
            cost_per_call = (total_cost / total_requests) if total_requests > 0 else 0.0

            adapter_metrics.update({
                "cost_per_call": round(cost_per_call, 6),
                "budget_used_percent": 0.0,  # Would need budget configuration
                "daily_budget_used_percent": 0.0,  # Would need budget configuration
                "monthly_budget_used_percent": 0.0,  # Would need budget configuration
                "budget_remaining_usd": 0.0,  # Would need budget configuration
                "budget_status": "ok" if total_cost < 100.0 else "warning"  # Simple threshold
            })

        # Add cost projections if requested
        if include_projections:
            daily_cost = adapter_metrics.get("daily_cost", 0.0)
            cost_projections = {
                "monthly_projection": {
                    "projected_cost": daily_cost * 30,
                    "confidence_level": 0.8 if daily_cost > 0 else 0.5
                }
            }
            adapter_metrics["cost_projections"] = cost_projections

        # Service now returns flat structure, add missing frontend fields
        from datetime import datetime

        # Get provider config for display name
        config = db.query(ProviderConfiguration).filter(
            text("provider_configurations.id = :id")
        ).params(id=str(adapter_id).replace('-', '')).first()

        provider_name = config.provider_name if config else "unknown"
        display_name = config.display_name if config else provider_name

        # Build flat response structure matching AdapterMetrics interface
        flat_response = {
            # Core identifiers
            "adapter_id": str(adapter_id),
            "provider_name": provider_name,
            "display_name": display_name,

            # Request metrics - use flat fields directly
            "total_requests": adapter_metrics.get("total_requests", 0),
            "successful_requests": adapter_metrics.get("successful_requests", 0),
            "failed_requests": adapter_metrics.get("failed_requests", 0),
            "success_rate": adapter_metrics.get("success_rate", 0.0),
            "average_response_time_ms": adapter_metrics.get("average_response_time_ms", 0.0),

            # Cost metrics - use flat fields directly
            "total_cost": float(adapter_metrics.get("total_cost", 0.0)),
            "daily_cost": float(adapter_metrics.get("daily_cost", 0.0)),
            "monthly_cost_estimate": float(adapter_metrics.get("monthly_cost_estimate", 0.0)),

            # Usage metrics - use flat fields directly
            "requests_today": adapter_metrics.get("requests_today", 0),
            "requests_this_hour": adapter_metrics.get("requests_this_hour", 0),

            # Status and timestamps - use flat fields directly
            "current_status": "healthy" if adapter_metrics.get("success_rate", 0) > 80.0 else "degraded" if adapter_metrics.get("total_requests", 0) > 0 else "down",
            "uptime_percentage": adapter_metrics.get("uptime_percentage", 0.0),
            "last_request_at": adapter_metrics.get("last_request_at"),
            "last_success_at": adapter_metrics.get("last_success_at"),
            "last_failure_at": adapter_metrics.get("last_failure_at"),

            # Additional metrics - use flat fields directly
            "rate_limit_hits": adapter_metrics.get("rate_limit_hits", 0),
            "error_rate_24h": adapter_metrics.get("error_rate_24h", 0.0),
            "p95_response_time_ms": adapter_metrics.get("p95_response_time_ms", 0.0),
        }

        return flat_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# T037: GET /api/v1/admin/adapters/{id}/health
@router.get("/{adapter_id}/health", response_model=AdapterHealthResponse)
async def get_adapter_health(
    adapter_id: UUID = Path(..., description="Adapter configuration ID"),
    force_check: Optional[bool] = Query(False, description="Force fresh health check"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get health status for a specific adapter.

    Optionally forces a fresh health check instead of using cached data.
    """
    try:
        # Get manager instances
        config_manager = ConfigurationManager(db)
        provider_manager = get_provider_manager(config_manager)

        # Check if configuration exists
        config = config_manager.get_provider_configuration(adapter_id)
        if not config:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        # Get health information
        if force_check:
            # Force a fresh health check
            health = await provider_manager.check_provider_health(str(adapter_id))
        else:
            # Use cached health data or perform check if needed
            health = await provider_manager.check_provider_health(str(adapter_id))

        # Convert provider name to enum with mapping for adapter registry names
        def map_provider_name_to_enum(provider_name: str) -> ProviderType:
            """Map adapter registry provider names to ProviderType enum values."""
            mapping = {
                "yfinance": ProviderType.YAHOO_FINANCE,
                "alpha_vantage": ProviderType.ALPHA_VANTAGE,
                "yahoo_finance": ProviderType.YAHOO_FINANCE,
                "iex_cloud": ProviderType.IEX_CLOUD,
                "polygon": ProviderType.POLYGON,
                "finnhub": ProviderType.FINNHUB,
            }
            return mapping.get(provider_name, ProviderType.YAHOO_FINANCE)

        provider_type = map_provider_name_to_enum(config.provider_name) if config.provider_name else ProviderType.YAHOO_FINANCE

        # Convert status to enum
        status_enum = AdapterHealthStatus(health.status.value) if hasattr(health.status, 'value') else AdapterHealthStatus(str(health.status))

        return AdapterHealthResponse(
            adapter_id=str(adapter_id),
            provider_name=provider_type,
            status=status_enum,
            last_check=datetime.fromtimestamp(health.last_check),
            success_rate=health.success_rate,
            avg_latency_ms=health.avg_latency_ms,
            error_count=health.error_count,
            circuit_breaker_state=health.circuit_breaker_state
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health for adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{adapter_id}/reset-metrics",
    response_model=dict,
    summary="Reset adapter metrics",
    description="Reset accumulated metrics for the specified adapter to clear stale data"
)
async def reset_adapter_metrics(
    adapter_id: str,
    current_admin: User = Depends(get_current_admin_user)
) -> dict:
    """Reset metrics for a specific adapter."""
    try:
        from src.services.config_manager import get_config_manager
        from src.services.adapters.metrics import get_metrics_collector

        config_manager = get_config_manager()
        metrics_collector = get_metrics_collector()

        # Check if configuration exists
        config = config_manager.get_provider_configuration(adapter_id)
        if not config:
            raise HTTPException(status_code=404, detail="Adapter configuration not found")

        # Reset metrics for this provider
        metrics_collector.reset_provider_metrics(config.provider_name)

        logger.info(f"Admin {current_admin.id} reset metrics for adapter {adapter_id}")

        return {"message": f"Metrics reset successfully for adapter {config.provider_name}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting metrics for adapter {adapter_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



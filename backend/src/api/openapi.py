"""
T067: Update OpenAPI specification with adapter endpoints
OpenAPI documentation for the market data adapter management API.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from src.schemas.adapter_schemas import (
    AdapterConfigurationResponse,
    AdapterConfigurationCreate,
    AdapterConfigurationUpdate,
    AdapterMetricsResponse,
    AdapterHealthResponse,
    ProviderRegistryResponse,
    ErrorResponse,
)


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema with adapter endpoints."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Portfolio Management API",
        version="0.2.0",
        description="""
        RESTful API for intelligent portfolio management system with real-time market data integration.

        ## Features
        - Portfolio Management: Create, edit, view multiple portfolios
        - Holdings Tracking: Add/remove stocks with quantity and cost basis
        - Performance Analytics: Real-time P&L, daily changes, allocation charts
        - Market Data Integration: Real-time price updates with provider management
        - Admin Dashboard: System administration and adapter management

        ## Authentication
        The API uses JWT bearer token authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your_jwt_token>
        ```

        ## Admin Endpoints
        Admin endpoints require a user with admin role for access.
        """,
        routes=app.routes,
    )

    # Add adapter-specific tags
    openapi_schema["tags"] = [
        {
            "name": "adapters",
            "description": "Market data adapter management"
        },
        {
            "name": "adapter-metrics",
            "description": "Adapter performance and usage metrics"
        },
        {
            "name": "adapter-health",
            "description": "Adapter health monitoring and status"
        },
        {
            "name": "provider-registry",
            "description": "Available market data provider registry"
        }
    ]

    # Enhanced error responses for adapter endpoints
    adapter_error_responses = {
        "400": {
            "description": "Bad Request - Invalid adapter configuration",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "examples": {
                        "validation_error": {
                            "summary": "Validation Error",
                            "value": {
                                "error": "validation_error",
                                "message": "Invalid adapter configuration",
                                "details": {
                                    "field": "api_key",
                                    "error": "API key is required for Alpha Vantage provider"
                                }
                            }
                        },
                        "provider_error": {
                            "summary": "Provider Error",
                            "value": {
                                "error": "provider_error",
                                "message": "Unsupported provider type",
                                "details": {
                                    "provider": "unknown_provider",
                                    "supported_providers": ["alpha_vantage", "yahoo_finance", "iex_cloud"]
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized - Authentication required",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "unauthorized",
                        "message": "Authentication required"
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden - Admin role required",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "forbidden",
                        "message": "Admin role required"
                    }
                }
            }
        },
        "404": {
            "description": "Not Found - Adapter not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "not_found",
                        "message": "Adapter not found"
                    }
                }
            }
        },
        "409": {
            "description": "Conflict - Adapter already exists",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "conflict",
                        "message": "Adapter with this name already exists"
                    }
                }
            }
        },
        "422": {
            "description": "Unprocessable Entity - Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "validation_error",
                        "message": "Request validation failed"
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "error": "internal_error",
                        "message": "An internal server error occurred"
                    }
                }
            }
        }
    }

    # Update adapter endpoints with enhanced documentation
    paths = openapi_schema.get("paths", {})

    # GET /api/v1/admin/adapters
    if "/api/v1/admin/adapters" in paths and "get" in paths["/api/v1/admin/adapters"]:
        paths["/api/v1/admin/adapters"]["get"].update({
            "tags": ["adapters"],
            "summary": "List Market Data Adapters",
            "description": """
            Retrieve a list of all configured market data adapters.

            Returns detailed information about each adapter including:
            - Configuration details (with sensitive fields masked)
            - Current status (active/inactive)
            - Creation and update timestamps
            - Provider information

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "responses": {
                "200": {
                    "description": "List of adapter configurations",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/AdapterConfigurationResponse"}
                            },
                            "example": [
                                {
                                    "id": "550e8400-e29b-41d4-a716-446655440001",
                                    "provider_name": "alpha_vantage",
                                    "display_name": "Alpha Vantage Primary",
                                    "description": "Primary Alpha Vantage adapter for real-time data",
                                    "config": {
                                        "api_key": "AV_***",
                                        "base_url": "https://www.alphavantage.co/query",
                                        "timeout": 30
                                    },
                                    "is_active": True,
                                    "priority": 1,
                                    "created_at": "2023-12-01T10:00:00Z",
                                    "updated_at": "2023-12-01T15:30:00Z"
                                }
                            ]
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # POST /api/v1/admin/adapters
    if "/api/v1/admin/adapters" in paths and "post" in paths["/api/v1/admin/adapters"]:
        paths["/api/v1/admin/adapters"]["post"].update({
            "tags": ["adapters"],
            "summary": "Create Market Data Adapter",
            "description": """
            Create a new market data adapter configuration.

            **Configuration Requirements**:
            - Each provider has specific required and optional configuration fields
            - API keys and sensitive data are automatically encrypted
            - Display names must be unique across all adapters
            - Priority determines fallback order (1 = highest priority)

            **Provider-Specific Config**:
            - **Alpha Vantage**: Requires `api_key`, optional `base_url`, `timeout`
            - **Yahoo Finance**: Optional `timeout`, `user_agent`, `max_retries`
            - **IEX Cloud**: Requires `api_token`, optional `sandbox`, `base_url`

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/AdapterConfigurationCreate"},
                        "examples": {
                            "alpha_vantage": {
                                "summary": "Alpha Vantage Adapter",
                                "value": {
                                    "provider_name": "alpha_vantage",
                                    "display_name": "Alpha Vantage Primary",
                                    "description": "Primary data source for real-time quotes",
                                    "config": {
                                        "api_key": "YOUR_ALPHA_VANTAGE_API_KEY",
                                        "base_url": "https://www.alphavantage.co/query",
                                        "timeout": 30
                                    },
                                    "is_active": True,
                                    "priority": 1
                                }
                            },
                            "yahoo_finance": {
                                "summary": "Yahoo Finance Adapter",
                                "value": {
                                    "provider_name": "yahoo_finance",
                                    "display_name": "Yahoo Finance Backup",
                                    "description": "Backup data source",
                                    "config": {
                                        "timeout": 15,
                                        "user_agent": "PortfolioManager/1.0"
                                    },
                                    "is_active": True,
                                    "priority": 2
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "201": {
                    "description": "Adapter created successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterConfigurationResponse"}
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # GET /api/v1/admin/adapters/{adapter_id}
    if "/api/v1/admin/adapters/{adapter_id}" in paths and "get" in paths["/api/v1/admin/adapters/{adapter_id}"]:
        paths["/api/v1/admin/adapters/{adapter_id}"]["get"].update({
            "tags": ["adapters"],
            "summary": "Get Adapter Details",
            "description": """
            Retrieve detailed information about a specific adapter.

            Returns complete adapter configuration with sensitive fields appropriately masked.

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter",
                    "example": "550e8400-e29b-41d4-a716-446655440001"
                }
            ],
            "responses": {
                "200": {
                    "description": "Adapter details",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterConfigurationResponse"}
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # PUT /api/v1/admin/adapters/{adapter_id}
    if "/api/v1/admin/adapters/{adapter_id}" in paths and "put" in paths["/api/v1/admin/adapters/{adapter_id}"]:
        paths["/api/v1/admin/adapters/{adapter_id}"]["put"].update({
            "tags": ["adapters"],
            "summary": "Update Adapter Configuration",
            "description": """
            Update an existing adapter configuration.

            **Partial Updates Supported**: Only provide fields you want to update.
            **Configuration Validation**: All provider-specific validation rules apply.
            **Sensitive Data**: API keys and secrets are re-encrypted if updated.

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter"
                }
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/AdapterConfigurationUpdate"},
                        "examples": {
                            "update_status": {
                                "summary": "Enable/Disable Adapter",
                                "value": {
                                    "is_active": False
                                }
                            },
                            "update_config": {
                                "summary": "Update Configuration",
                                "value": {
                                    "display_name": "Updated Alpha Vantage",
                                    "config": {
                                        "timeout": 45
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Adapter updated successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterConfigurationResponse"}
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # DELETE /api/v1/admin/adapters/{adapter_id}
    if "/api/v1/admin/adapters/{adapter_id}" in paths and "delete" in paths["/api/v1/admin/adapters/{adapter_id}"]:
        paths["/api/v1/admin/adapters/{adapter_id}"]["delete"].update({
            "tags": ["adapters"],
            "summary": "Delete Adapter",
            "description": """
            Delete an adapter configuration.

            **Warning**: This action is irreversible. All configuration data and historical metrics
            associated with this adapter will be permanently deleted.

            **Active Adapters**: You must deactivate an adapter before deletion.

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter"
                }
            ],
            "responses": {
                "204": {
                    "description": "Adapter deleted successfully"
                },
                **adapter_error_responses
            }
        })

    # GET /api/v1/admin/adapters/{adapter_id}/metrics
    if "/api/v1/admin/adapters/{adapter_id}/metrics" in paths:
        paths["/api/v1/admin/adapters/{adapter_id}/metrics"]["get"].update({
            "tags": ["adapter-metrics"],
            "summary": "Get Adapter Metrics",
            "description": """
            Retrieve performance and usage metrics for a specific adapter.

            **Metrics Include**:
            - Request counts (total, successful, failed)
            - Response times (average, percentiles)
            - Success rates and error rates
            - Cost tracking and usage statistics
            - Recent activity timestamps

            **Time Range**: Use the `timeRange` parameter to specify the metrics window.

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter"
                },
                {
                    "name": "timeRange",
                    "in": "query",
                    "required": False,
                    "schema": {
                        "type": "string",
                        "enum": ["1h", "24h", "7d", "30d"],
                        "default": "24h"
                    },
                    "description": "Time range for metrics aggregation"
                }
            ],
            "responses": {
                "200": {
                    "description": "Adapter metrics data",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterMetricsResponse"},
                            "example": {
                                "adapter_id": "550e8400-e29b-41d4-a716-446655440001",
                                "provider_name": "alpha_vantage",
                                "display_name": "Alpha Vantage Primary",
                                "total_requests": 1547,
                                "successful_requests": 1489,
                                "failed_requests": 58,
                                "success_rate": 96.25,
                                "average_response_time_ms": 142.3,
                                "p95_response_time_ms": 284.1,
                                "total_cost": 12.47,
                                "daily_cost": 2.15,
                                "monthly_cost_estimate": 64.50,
                                "requests_today": 89,
                                "requests_this_hour": 12,
                                "last_request_at": "2023-12-01T16:45:30Z",
                                "last_success_at": "2023-12-01T16:45:30Z",
                                "last_failure_at": "2023-12-01T14:22:15Z",
                                "current_status": "healthy",
                                "uptime_percentage": 99.2,
                                "rate_limit_hits": 3,
                                "error_rate_24h": 2.1
                            }
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # GET /api/v1/admin/adapters/{adapter_id}/health
    if "/api/v1/admin/adapters/{adapter_id}/health" in paths:
        paths["/api/v1/admin/adapters/{adapter_id}/health"]["get"].update({
            "tags": ["adapter-health"],
            "summary": "Get Adapter Health Status",
            "description": """
            Retrieve current health status and monitoring information for an adapter.

            **Health Checks Include**:
            - Connectivity tests to provider APIs
            - Authentication validation
            - Rate limit status
            - Response time monitoring
            - Overall adapter status

            **Status Types**:
            - `healthy`: All checks passing, adapter fully operational
            - `degraded`: Some issues detected but adapter still functional
            - `down`: Critical issues, adapter not operational

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter"
                }
            ],
            "responses": {
                "200": {
                    "description": "Adapter health status",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterHealthResponse"},
                            "example": {
                                "adapter_id": "550e8400-e29b-41d4-a716-446655440001",
                                "provider_name": "alpha_vantage",
                                "display_name": "Alpha Vantage Primary",
                                "overall_status": "healthy",
                                "last_check_at": "2023-12-01T16:50:00Z",
                                "uptime_percentage": 99.2,
                                "next_check_in": 240,
                                "check_interval": 300,
                                "consecutive_failures": 0,
                                "last_success_at": "2023-12-01T16:50:00Z",
                                "last_failure_at": "2023-11-30T08:15:30Z",
                                "checks": [
                                    {
                                        "check_type": "connectivity",
                                        "status": "healthy",
                                        "message": "Connection successful",
                                        "response_time_ms": 89.2,
                                        "checked_at": "2023-12-01T16:50:00Z"
                                    },
                                    {
                                        "check_type": "authentication",
                                        "status": "healthy",
                                        "message": "API key valid",
                                        "checked_at": "2023-12-01T16:50:00Z"
                                    }
                                ]
                            }
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # POST /api/v1/admin/adapters/{adapter_id}/health
    if "/api/v1/admin/adapters/{adapter_id}/health" in paths and "post" in paths["/api/v1/admin/adapters/{adapter_id}/health"]:
        paths["/api/v1/admin/adapters/{adapter_id}/health"]["post"].update({
            "tags": ["adapter-health"],
            "summary": "Trigger Health Check",
            "description": """
            Manually trigger a health check for the specified adapter.

            This forces an immediate health check outside of the regular monitoring schedule.
            Useful for:
            - Testing after configuration changes
            - Verifying fixes after issues
            - Manual monitoring during maintenance

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "parameters": [
                {
                    "name": "adapter_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                    "description": "Unique identifier of the adapter"
                }
            ],
            "responses": {
                "200": {
                    "description": "Health check completed",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AdapterHealthResponse"}
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # GET /api/v1/admin/adapters/registry
    if "/api/v1/admin/adapters/registry" in paths:
        paths["/api/v1/admin/adapters/registry"]["get"].update({
            "tags": ["provider-registry"],
            "summary": "Get Provider Registry",
            "description": """
            Retrieve information about all available market data providers.

            **Provider Information Includes**:
            - Display names and descriptions
            - Required and optional configuration fields
            - Capabilities (real-time, historical, bulk support)
            - Rate limits and quotas
            - API documentation links

            Use this endpoint to discover available providers and their configuration requirements
            before creating new adapters.

            **Admin Access Required**: This endpoint requires admin role.
            """,
            "responses": {
                "200": {
                    "description": "Provider registry information",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProviderRegistryResponse"},
                            "example": {
                                "providers": {
                                    "alpha_vantage": {
                                        "name": "alpha_vantage",
                                        "display_name": "Alpha Vantage",
                                        "description": "Professional-grade financial market data",
                                        "required_config": ["api_key"],
                                        "optional_config": ["base_url", "timeout"],
                                        "supports_bulk": True,
                                        "rate_limits": {
                                            "requests_per_minute": 5,
                                            "requests_per_day": 500,
                                            "symbols_per_request": 100
                                        }
                                    },
                                    "yahoo_finance": {
                                        "name": "yahoo_finance",
                                        "display_name": "Yahoo Finance",
                                        "description": "Free financial data provider",
                                        "required_config": [],
                                        "optional_config": ["timeout", "user_agent"],
                                        "supports_bulk": True,
                                        "rate_limits": {
                                            "requests_per_minute": 60,
                                            "symbols_per_request": 50
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                **adapter_error_responses
            }
        })

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from login endpoint"
        }
    }

    # Apply security to all adapter endpoints
    for path, path_item in paths.items():
        if path.startswith("/api/v1/admin/adapters"):
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete"]:
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi_docs(app: FastAPI) -> None:
    """Setup OpenAPI documentation for the FastAPI app."""
    app.openapi = lambda: custom_openapi(app)

    # Add additional metadata
    app.title = "Portfolio Management API"
    app.description = "RESTful API for intelligent portfolio management with market data adapter system"
    app.version = "0.2.0"
    app.contact = {
        "name": "Portfolio Management System",
        "email": "support@portfoliomanagement.com",
    }
    app.license_info = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
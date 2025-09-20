"""
Custom exceptions and error handling for the portfolio management system.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging


class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""
    
    def __init__(self, message: str, code: str = "PORTFOLIO_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class PortfolioNotFoundError(PortfolioError):
    """Raised when a portfolio is not found."""
    
    def __init__(self, portfolio_id: str):
        super().__init__(
            message=f"Portfolio with ID {portfolio_id} not found",
            code="PORTFOLIO_NOT_FOUND",
            details={"portfolio_id": portfolio_id}
        )


class TransactionError(Exception):
    """Base exception for transaction-related errors."""
    
    def __init__(self, message: str, code: str = "TRANSACTION_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class InsufficientFundsError(TransactionError):
    """Raised when trying to sell more shares than available."""
    
    def __init__(self, symbol: str, requested: float, available: float):
        super().__init__(
            message=f"Insufficient shares for {symbol}: requested {requested}, available {available}",
            code="INSUFFICIENT_SHARES",
            details={"symbol": symbol, "requested": requested, "available": available}
        )


class InsufficientSharesError(TransactionError):
    """Raised when trying to sell more shares than available (alias for compatibility)."""
    
    def __init__(self, symbol: str, requested: str, available: str):
        super().__init__(
            message=f"Insufficient shares for {symbol}: requested {requested}, available {available}",
            code="INSUFFICIENT_SHARES",
            details={"symbol": symbol, "requested": requested, "available": available}
        )


class StockNotFoundError(Exception):
    """Raised when a stock is not found."""
    
    def __init__(self, symbol: str):
        self.message = f"Stock with symbol {symbol} not found"
        self.code = "STOCK_NOT_FOUND"
        self.details = {"symbol": symbol}
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised for validation errors."""
    
    def __init__(self, message: str, field: str, value: Any):
        self.message = message
        self.code = "VALIDATION_ERROR"
        self.details = {"field": field, "value": value}
        super().__init__(self.message)


def create_error_response(
    status_code: int,
    message: str,
    code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        "error": {
            "message": message,
            "code": code,
            "details": details or {}
        }
    }
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def portfolio_exception_handler(request: Request, exc: PortfolioError) -> JSONResponse:
    """Handle portfolio-related exceptions."""
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def transaction_exception_handler(request: Request, exc: TransactionError) -> JSONResponse:
    """Handle transaction-related exceptions."""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def stock_not_found_exception_handler(request: Request, exc: StockNotFoundError) -> JSONResponse:
    """Handle stock not found exceptions."""
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        code="INTERNAL_ERROR",
        details={"type": type(exc).__name__}
    )


# Adapter-specific exceptions
class AdapterError(Exception):
    """Base exception for adapter-related errors."""

    def __init__(self, message: str, code: str = "ADAPTER_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AdapterConfigurationError(AdapterError):
    """Exception for adapter configuration errors."""

    def __init__(self, message: str, provider_name: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if provider_name:
            details["provider_name"] = provider_name
        super().__init__(message, "ADAPTER_CONFIG_ERROR", details)


class AdapterConnectionError(AdapterError):
    """Exception for adapter connection failures."""

    def __init__(self, message: str, provider_name: str = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if provider_name:
            details["provider_name"] = provider_name
        super().__init__(message, "ADAPTER_CONNECTION_ERROR", details)


class AdapterValidationError(AdapterError):
    """Exception for adapter validation failures."""

    def __init__(self, message: str, validation_errors: list = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(message, "ADAPTER_VALIDATION_ERROR", details)


class AdapterRateLimitError(AdapterError):
    """Exception for adapter rate limiting."""

    def __init__(self, message: str, provider_name: str = None, retry_after: int = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if provider_name:
            details["provider_name"] = provider_name
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "ADAPTER_RATE_LIMIT_ERROR", details)


# Adapter exception handlers
async def adapter_error_handler(request: Request, exc: AdapterError) -> JSONResponse:
    """Handle adapter-related exceptions."""
    logger = logging.getLogger("adapter.exception.handler")

    # Log the adapter error with context
    logger.error(f"Adapter error: {exc.message}", extra={
        "error_code": exc.code,
        "error_details": exc.details,
        "request_path": str(request.url.path),
        "request_method": request.method
    })

    # Map adapter errors to appropriate HTTP status codes
    status_code_map = {
        "ADAPTER_CONFIG_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "ADAPTER_CONNECTION_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "ADAPTER_VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "ADAPTER_RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
        "ADAPTER_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR
    }

    status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return create_error_response(
        status_code=status_code,
        message=exc.message,
        code=exc.code,
        details=exc.details
    )


async def adapter_configuration_error_handler(request: Request, exc: AdapterConfigurationError) -> JSONResponse:
    """Handle adapter configuration exceptions."""
    return await adapter_error_handler(request, exc)


async def adapter_connection_error_handler(request: Request, exc: AdapterConnectionError) -> JSONResponse:
    """Handle adapter connection exceptions."""
    return await adapter_error_handler(request, exc)


async def adapter_validation_error_handler(request: Request, exc: AdapterValidationError) -> JSONResponse:
    """Handle adapter validation exceptions."""
    return await adapter_error_handler(request, exc)


async def adapter_rate_limit_error_handler(request: Request, exc: AdapterRateLimitError) -> JSONResponse:
    """Handle adapter rate limit exceptions."""
    return await adapter_error_handler(request, exc)
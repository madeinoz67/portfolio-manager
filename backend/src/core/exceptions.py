"""
Custom exceptions and error handling for the portfolio management system.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


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
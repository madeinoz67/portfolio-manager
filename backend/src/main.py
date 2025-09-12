"""
FastAPI application entry point for Portfolio Management System.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.portfolios import router as portfolios_router
from src.api.stocks import router as stocks_router
from src.api.transactions import router as transactions_router
from src.api.performance import router as performance_router
from src.core.exceptions import (
    PortfolioError,
    TransactionError,
    StockNotFoundError,
    ValidationError,
    portfolio_exception_handler,
    transaction_exception_handler,
    stock_not_found_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from src.core.logging import setup_logging, set_request_id, get_logger
from src.database import engine, Base

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Management API",
    description="RESTful API for intelligent portfolio management system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add exception handlers
app.add_exception_handler(PortfolioError, portfolio_exception_handler)
app.add_exception_handler(TransactionError, transaction_exception_handler)
app.add_exception_handler(StockNotFoundError, stock_not_found_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = set_request_id()
    logger.info(f"Request started: {request.method} {request.url}", extra={"request_id": request_id})
    
    try:
        response = await call_next(request)
        logger.info(f"Request completed: {response.status_code}", extra={"request_id": request_id})
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", extra={"request_id": request_id})
        raise

# Database startup event
@app.on_event("startup")
async def create_tables():
    """Create database tables on application startup."""
    logger.info("Creating database tables...")
    try:
        # Import all models to ensure they're registered with Base
        from src.models import user, portfolio, stock, transaction, holding  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Include API routers
app.include_router(portfolios_router)
app.include_router(stocks_router)
app.include_router(transactions_router)
app.include_router(performance_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API information."""
    return {
        "message": "Portfolio Management API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

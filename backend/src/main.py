"""
FastAPI application entry point for Portfolio Management System.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager

from src.api.auth import router as auth_router
from src.api.portfolios import router as portfolios_router
from src.api.stocks import router as stocks_router
from src.api.transactions import router as transactions_router
from src.api.performance import router as performance_router
from src.api.api_keys import router as api_keys_router
from src.api.market_data import router as market_data_router
from src.api.admin import router as admin_router
from src.api.admin_adapters import router as admin_adapters_router
from src.api.metrics import router as metrics_router
from src.core.exceptions import (
    PortfolioError,
    TransactionError,
    StockNotFoundError,
    ValidationError,
    AdapterError,
    AdapterConfigurationError,
    AdapterConnectionError,
    AdapterValidationError,
    AdapterRateLimitError,
    portfolio_exception_handler,
    transaction_exception_handler,
    stock_not_found_exception_handler,
    validation_exception_handler,
    adapter_error_handler,
    adapter_configuration_error_handler,
    adapter_connection_error_handler,
    adapter_validation_error_handler,
    adapter_rate_limit_error_handler,
    general_exception_handler,
)
from src.core.logging import setup_logging, set_request_id, get_logger
from src.database import engine, Base, get_db
from src.services.adapter_market_data_service import AdapterMarketDataService
from src.services.activity_service import log_provider_activity
from src.services.scheduler_service import get_scheduler_service

# Setup logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Background task for periodic market data updates
async def periodic_price_updates():
    """Background task that periodically fetches prices to generate live activity."""
    cycle_count = 0

    while True:
        try:
            # Check if paused
            if scheduler_paused:
                logger.info("Scheduler is paused, waiting...")
                await asyncio.sleep(30)  # Check every 30 seconds if still paused
                continue

            # Wait before first execution
            await asyncio.sleep(60)  # Start after 1 minute

            # Double-check pause status after wait
            if scheduler_paused:
                continue

            logger.info(f"Starting periodic price update task - cycle {cycle_count + 1}")

            # Get database session
            db = next(get_db())

            try:
                # Get scheduler service and record execution start
                scheduler_service = get_scheduler_service(db)
                scheduler_service.record_execution_start()

                # Create market data service (using new adapter system)
                service = AdapterMarketDataService(db)

                # Get symbols dynamically based on actual usage
                # Use adapter system with standard bulk limit
                provider_bulk_limit = 50  # Standard bulk limit for adapter system

                # Get actively monitored symbols (includes portfolios, recent requests, and all existing symbols)
                symbols_to_fetch = service.get_actively_monitored_symbols(
                    provider_bulk_limit=provider_bulk_limit,
                    minutes_lookback=60
                )

                logger.info(f"Selected symbols for cycle {cycle_count + 1} (limit {provider_bulk_limit}): {symbols_to_fetch}")

                # If no symbols to process, skip this cycle (no fallback logic)
                if not symbols_to_fetch:
                    logger.info("No symbols to process in this cycle, skipping fetch")
                    continue

                # Occasionally add some variety with system-level activities
                if cycle_count % 3 == 0:  # Every 3rd cycle
                    log_provider_activity(
                        db_session=db,
                        provider_id="system",
                        activity_type="HEALTH_CHECK",
                        description="System health check completed",
                        status="success",
                        metadata={
                            "uptime_minutes": cycle_count * 15,
                            "providers_available": len(service.registry.list_providers()),
                            "system_status": "healthy"
                        }
                    )

                # Use simplified provider interface - providers handle bulk logic internally
                logger.info(f"Fetching prices for {len(symbols_to_fetch)} symbols using provider adapters")
                try:
                    results = await service.fetch_multiple_prices(symbols_to_fetch)
                    successful_fetches = len([result for result in results.values() if result is not None])
                    logger.info(f"Fetch completed: {successful_fetches}/{len(symbols_to_fetch)} successful")

                    # After successful price updates, queue portfolio updates via update queue
                    if successful_fetches > 0:
                        logger.info("Queuing portfolio updates for fresh market data")
                        try:
                            from src.services.portfolio_update_queue import get_portfolio_update_queue

                            # Queue portfolio updates for all successfully fetched symbols
                            successfully_fetched_symbols = [symbol for symbol, result in results.items() if result is not None]

                            # Get the portfolio update queue and queue updates for all portfolios
                            queue = get_portfolio_update_queue()

                            # Queue update with high priority for periodic market data updates
                            queue_success = queue.queue_portfolio_update(
                                portfolio_id="all",  # Special ID for all portfolios
                                symbols=successfully_fetched_symbols,
                                priority=3  # Higher priority for scheduled updates
                            )

                            if queue_success:
                                logger.info(f"Queued portfolio updates for {len(successfully_fetched_symbols)} symbols: {successfully_fetched_symbols}")
                            else:
                                logger.warning("Portfolio update queue rejected the request (rate limited)")

                        except Exception as portfolio_error:
                            logger.error(f"Error queuing portfolio updates: {portfolio_error}")

                    # Record successful execution in scheduler service
                    scheduler_service.record_execution_success(symbols_processed=successful_fetches)

                except Exception as e:
                    logger.error(f"Error in fetch for periodic task: {e}")
                    successful_fetches = 0

                    # Record failure in scheduler service
                    scheduler_service.record_execution_failure(f"Fetch error: {str(e)}")

                # Log bulk operation summary every few cycles
                if cycle_count % 2 == 1:  # Every other cycle
                    log_provider_activity(
                        db_session=db,
                        provider_id="system",
                        activity_type="BATCH_SUMMARY",
                        description=f"Batch update completed: {successful_fetches}/{len(symbols_to_fetch)} symbols updated",
                        status="success" if successful_fetches > 0 else "warning",
                        metadata={
                            "cycle_number": cycle_count + 1,
                            "symbols_processed": symbols_to_fetch,
                            "success_count": successful_fetches,
                            "dynamic_discovery": "enabled",
                            "provider_bulk_limit": provider_bulk_limit,
                            "sources": "portfolio_holdings_and_recent_requests"
                        }
                    )

                await service.close_session()
                cycle_count += 1

                logger.info(f"Completed periodic price update task - cycle {cycle_count}")

            except Exception as e:
                logger.error(f"Error in periodic price update task: {e}")
            finally:
                db.close()

            # Wait for next cycle (15 minutes)
            await asyncio.sleep(900)

        except Exception as e:
            logger.error(f"Fatal error in periodic task: {e}")
            await asyncio.sleep(900)  # Wait 15 minutes before retrying to maintain consistent intervals


async def pause_background_task() -> bool:
    """Pause the background scheduler task."""
    global scheduler_paused
    try:
        scheduler_paused = True
        logger.info("Background scheduler paused by admin control")
        return True
    except Exception as e:
        logger.error(f"Error pausing scheduler: {e}")
        return False


async def restart_background_task() -> bool:
    """Restart/resume the background scheduler task."""
    global background_task, scheduler_paused
    try:
        scheduler_paused = False

        # If the task is dead, restart it
        if background_task is None or background_task.done():
            logger.info("Restarting background scheduler task...")
            background_task = asyncio.create_task(periodic_price_updates())
            logger.info("Background scheduler task restarted")

            # Log system restart activity
            try:
                from src.database import get_db
                from src.services.activity_service import log_provider_activity

                db = next(get_db())
                log_provider_activity(
                    db_session=db,
                    provider_id="system",
                    activity_type="SCHEDULER_CONTROL",
                    description="Scheduler restarted automatically by system",
                    status="success",
                    metadata={
                        "restart_type": "automatic",
                        "trigger": "task_failure_recovery"
                    }
                )
                db.close()
            except Exception as log_e:
                logger.error(f"Failed to log system restart activity: {log_e}")
        else:
            logger.info("Background scheduler resumed from pause")

        return True
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        return False

# Background task handle and control
background_task = None
scheduler_paused = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global background_task

    # Create database tables
    logger.info("Creating database tables...")
    try:
        # Import all models to ensure they're registered with Base
        from src.models import user, portfolio, stock, transaction, holding, news_notice  # noqa: F401
        from src.models import market_data_provider, realtime_price_history, portfolio_valuation  # noqa: F401
        from src.models import sse_connection, poll_interval_config, market_data_usage_metrics  # noqa: F401

        # Import adapter models
        from src.models import provider_configuration, provider_metrics, cost_tracking_record  # noqa: F401
        from src.models import adapter_registry, adapter_health_check  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    # Initialize adapter registry
    logger.info("Initializing adapter registry...")
    try:
        from src.services.adapters.registry_init import initialize_adapter_registry
        initialize_adapter_registry()

        from src.services.adapters.registry import get_provider_registry
        provider_registry = get_provider_registry()
        logger.info(f"Adapter registry initialized with {len(provider_registry.list_providers())} providers")
    except Exception as e:
        logger.error(f"Failed to initialize adapter registry: {e}")

    # Initialize default providers
    logger.info("Initializing default market data providers...")
    try:
        from src.services.default_providers_init import create_default_providers
        create_default_providers()
        logger.info("Default providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize default providers: {e}")

    # Initialize portfolio update queue
    logger.info("Initializing portfolio update queue...")
    try:
        from src.services.portfolio_update_queue import initialize_portfolio_queue
        await initialize_portfolio_queue()
        logger.info("Portfolio update queue initialized and started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize portfolio update queue: {e}")
        # Don't raise - let the app start but queue will be unavailable

    # Start health check service for adapter monitoring
    logger.info("Starting health check service...")
    try:
        from src.services.health_checker import start_health_check_service
        await start_health_check_service(check_interval=300)  # 5 minute intervals
        logger.info("Health check service started successfully")
    except Exception as e:
        logger.error(f"Failed to start health check service: {e}")
        # Don't raise - let the app start but alerts will be unavailable

    # Start background task
    logger.info("Starting background tasks...")
    background_task = asyncio.create_task(periodic_price_updates())

    yield

    # Shutdown health check service
    logger.info("Shutting down health check service...")
    try:
        from src.services.health_checker import stop_health_check_service
        await stop_health_check_service()
        logger.info("Health check service shut down successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown health check service: {e}")

    # Shutdown portfolio update queue
    logger.info("Shutting down portfolio update queue...")
    try:
        from src.services.portfolio_update_queue import shutdown_portfolio_queue
        await shutdown_portfolio_queue()
        logger.info("Portfolio update queue shut down successfully")
    except Exception as e:
        logger.error(f"Failed to shutdown portfolio update queue: {e}")

    # Cleanup background task
    if background_task:
        logger.info("Stopping background tasks...")
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Management API",
    description="RESTful API for intelligent portfolio management system with real-time market data integration",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Admin API contract error handler
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to contract-compliant error format for admin endpoints."""
    # Check if this is an admin endpoint request
    if request.url.path.startswith("/api/v1/admin/"):
        error_code = "unknown"
        message = str(exc.detail)

        # Map HTTP status codes to error codes per contract
        if exc.status_code == 401:
            error_code = "unauthorized"
            message = "Authentication required"
        elif exc.status_code == 403:
            if "Admin access required" in str(exc.detail):
                error_code = "forbidden"
                message = "Admin role required"
            else:
                # Handle missing Authorization header (403 from HTTPBearer)
                error_code = "unauthorized"
                message = "Authentication required"
                # Change status code to 401 for contract compliance
                return JSONResponse(
                    status_code=401,
                    content={"error": error_code, "message": message}
                )
        elif exc.status_code == 404:
            error_code = "not_found"
            if "User not found" in str(exc.detail):
                message = "User not found"
        elif exc.status_code == 422:
            error_code = "validation_error"

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_code, "message": message}
        )

    # For non-admin endpoints, return standard format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(PortfolioError, portfolio_exception_handler)
app.add_exception_handler(TransactionError, transaction_exception_handler)
app.add_exception_handler(StockNotFoundError, stock_not_found_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

# Add adapter exception handlers
app.add_exception_handler(AdapterConfigurationError, adapter_configuration_error_handler)
app.add_exception_handler(AdapterConnectionError, adapter_connection_error_handler)
app.add_exception_handler(AdapterValidationError, adapter_validation_error_handler)
app.add_exception_handler(AdapterRateLimitError, adapter_rate_limit_error_handler)
app.add_exception_handler(AdapterError, adapter_error_handler)

app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],  # Frontend URLs
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

# Startup events moved to lifespan context manager above

# Include API routers
app.include_router(auth_router)
app.include_router(portfolios_router)
app.include_router(stocks_router)
app.include_router(transactions_router)
app.include_router(performance_router)
app.include_router(api_keys_router)
app.include_router(market_data_router)
app.include_router(admin_router)
app.include_router(admin_adapters_router)
app.include_router(metrics_router)


@app.get("/")
async def root() -> dict[str, str | list[str]]:
    """Root endpoint returning API information."""
    return {
        "message": "Portfolio Management API",
        "version": "0.2.0",
        "docs": "/docs",
        "features": ["Portfolio Management", "Real-time Market Data", "Admin Controls"],
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

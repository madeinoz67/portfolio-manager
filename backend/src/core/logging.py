"""
Structured logging configuration for the portfolio management system.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict
import json
from contextvars import ContextVar
import uuid
from datetime import datetime


# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra') and record.extra:
            log_entry["extra"] = record.extra
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """Setup structured logging configuration."""
    
    # Create formatter
    formatter = StructuredFormatter()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """Log a message with additional context."""
    extra = {"extra": kwargs} if kwargs else {}
    getattr(logger, level.lower())(message, extra=extra)


def set_request_id(request_id: str = None) -> str:
    """Set the request ID for the current context."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_var.get()


class LoggerMixin:
    """Mixin to add structured logging to classes."""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        return self._logger
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log an info message with context."""
        log_with_context(self.logger, "info", message, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message with context."""
        log_with_context(self.logger, "warning", message, **kwargs)
    
    def log_error(self, message: str, **kwargs) -> None:
        """Log an error message with context."""
        log_with_context(self.logger, "error", message, **kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log a debug message with context."""
        log_with_context(self.logger, "debug", message, **kwargs)
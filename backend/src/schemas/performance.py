"""
Performance API schemas for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class PerformancePeriod(str, Enum):
    """Valid performance periods."""
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    YEAR_TO_DATE = "YTD"
    ALL = "ALL"


class PerformanceMetrics(BaseModel):
    """Schema for portfolio performance metrics."""
    total_return: Decimal
    annualized_return: Decimal
    max_drawdown: Decimal
    dividend_yield: Decimal
    period_start_value: Decimal
    period_end_value: Decimal
    total_dividends: Decimal
    period: str
    calculated_at: datetime

    class Config:
        from_attributes = True
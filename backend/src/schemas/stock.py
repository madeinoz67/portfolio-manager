"""
Stock API schemas for validation and serialization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.models.stock import StockStatus
from src.utils.datetime_utils import to_iso_string


class StockResponse(BaseModel):
    """Schema for stock API responses."""
    id: UUID
    symbol: str
    company_name: str
    exchange: str = "ASX"
    current_price: Optional[Decimal] = None
    daily_change: Optional[Decimal] = None
    daily_change_percent: Optional[Decimal] = None
    status: StockStatus = StockStatus.ACTIVE
    last_price_update: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def convert_timestamp(cls, data: Any) -> Any:
        """Convert datetime fields to consistent ISO string format."""
        if hasattr(data, '__dict__'):
            # Handle SQLAlchemy objects
            if hasattr(data, 'last_price_update') and data.last_price_update is not None:
                data.last_price_update = to_iso_string(data.last_price_update)
        elif isinstance(data, dict):
            # Handle dict data
            if 'last_price_update' in data and data['last_price_update'] is not None:
                data['last_price_update'] = to_iso_string(data['last_price_update'])
        return data

    class Config:
        from_attributes = True


class StockDetailResponse(StockResponse):
    """Schema for detailed stock API responses."""
    previous_close: Optional[Decimal] = None
    volume: Optional[int] = None

    class Config:
        from_attributes = True


class StockCreateRequest(BaseModel):
    """Schema for creating a new stock."""
    symbol: str = Field(..., max_length=10)
    company_name: str = Field(..., max_length=200)
    exchange: str = Field(default="ASX", max_length=50)
    current_price: Optional[Decimal] = Field(None, ge=0)
    status: StockStatus = StockStatus.ACTIVE

    class Config:
        from_attributes = True


class PricePointResponse(BaseModel):
    """Schema for stock price history points."""
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Decimal
    volume: Optional[int] = None

    class Config:
        from_attributes = True
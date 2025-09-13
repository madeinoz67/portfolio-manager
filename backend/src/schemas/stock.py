"""
Stock API schemas for validation and serialization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.stock import StockStatus


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
    last_price_update: Optional[datetime] = None

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
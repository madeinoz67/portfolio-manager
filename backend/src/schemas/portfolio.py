"""
Portfolio API schemas for validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from src.utils.datetime_utils import to_iso_string


class PortfolioCreate(BaseModel):
    """Schema for creating a new portfolio."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class PortfolioDeleteConfirmation(BaseModel):
    """Schema for portfolio deletion with confirmation."""
    confirmation_name: str = Field(..., min_length=1, max_length=100)


class PortfolioResponse(BaseModel):
    """Schema for portfolio API responses."""
    id: UUID
    name: str
    description: Optional[str] = None
    total_value: Decimal = Field(default=Decimal("0.00"))
    daily_change: Decimal = Field(default=Decimal("0.00"))
    daily_change_percent: Decimal = Field(default=Decimal("0.00"))
    created_at: datetime
    updated_at: datetime
    price_last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: to_iso_string
        }
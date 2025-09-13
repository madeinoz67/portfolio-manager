"""
Holding schemas for serialization and validation.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.stock import StockResponse


class HoldingBase(BaseModel):
    """Base holding schema with common fields."""
    quantity: Decimal = Field(..., description="Number of shares held")
    average_cost: Decimal = Field(..., description="Average cost per share")
    current_value: Decimal = Field(..., description="Current total value of holding")
    unrealized_gain_loss: Decimal = Field(..., description="Unrealized gain or loss")
    unrealized_gain_loss_percent: Decimal = Field(..., description="Unrealized gain or loss percentage")


class HoldingResponse(HoldingBase):
    """Response schema for holding data."""
    id: UUID = Field(..., description="Unique holding identifier")
    portfolio_id: UUID = Field(..., description="Portfolio identifier")
    stock: StockResponse = Field(..., description="Stock information")
    created_at: datetime = Field(..., description="When the holding was created")
    updated_at: datetime = Field(..., description="When the holding was last updated")
    recent_news_count: int = Field(default=0, description="Number of recent news/notices (last 30 days)")

    model_config = {"from_attributes": True}


class HoldingCreate(HoldingBase):
    """Schema for creating a new holding."""
    stock_id: UUID = Field(..., description="Stock identifier")


class HoldingUpdate(BaseModel):
    """Schema for updating a holding."""
    quantity: Decimal | None = Field(None, description="Number of shares held")
    average_cost: Decimal | None = Field(None, description="Average cost per share")
    current_value: Decimal | None = Field(None, description="Current total value of holding")
    unrealized_gain_loss: Decimal | None = Field(None, description="Unrealized gain or loss")
    unrealized_gain_loss_percent: Decimal | None = Field(None, description="Unrealized gain or loss percentage")
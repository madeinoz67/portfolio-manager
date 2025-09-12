"""
Transaction API schemas for validation and serialization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.models.transaction import TransactionType, SourceType
from src.schemas.stock import StockResponse


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    stock_symbol: str = Field(..., min_length=1, max_length=10)
    transaction_type: TransactionType
    quantity: Decimal = Field(..., gt=0)
    price_per_share: Decimal = Field(..., gt=0)
    fees: Decimal = Field(default=Decimal("0.00"), ge=0)
    transaction_date: date
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        if v > date.today():
            raise ValueError('Transaction date cannot be in the future')
        return v


class TransactionResponse(BaseModel):
    """Schema for transaction API responses."""
    id: UUID
    stock: StockResponse
    transaction_type: TransactionType
    quantity: Decimal
    price_per_share: Decimal
    total_amount: Decimal
    fees: Decimal
    transaction_date: date
    source_type: SourceType
    notes: Optional[str] = None
    is_verified: bool
    processed_date: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list responses."""
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
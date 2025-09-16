"""
Transaction API schemas for validation and serialization.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.models.transaction import TransactionType, SourceType
from src.schemas.stock import StockResponse
from src.utils.datetime_utils import now


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    stock_symbol: str = Field(..., min_length=1, max_length=10)
    transaction_type: TransactionType
    quantity: Decimal = Field(..., ge=0)
    price_per_share: Decimal = Field(..., ge=0)
    fees: Decimal = Field(default=Decimal("0.00"), ge=0)
    transaction_date: Union[date, datetime, str]
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('transaction_date', pre=True)
    def validate_transaction_date(cls, v):
        """
        Handle datetime strings from frontend and convert to date.
        Accepts: date objects, datetime objects, or ISO datetime strings.
        Always returns a date object.
        """
        if isinstance(v, str):
            # Parse ISO datetime string (e.g., "2025-09-14T16:00:00.000Z")
            try:
                # Try parsing as datetime first
                if 'T' in v:
                    parsed_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    result_date = parsed_dt.date()
                else:
                    # Parse as date-only string
                    result_date = datetime.fromisoformat(v).date()
            except ValueError:
                raise ValueError(f'Invalid date format: {v}. Expected ISO date or datetime string.')
        elif isinstance(v, datetime):
            # Extract date from datetime
            result_date = v.date()
        elif isinstance(v, date):
            # Already a date
            result_date = v
        else:
            raise ValueError(f'Invalid date type: {type(v)}. Expected date, datetime, or string.')

        # Validate date is not in the future
        # Users enter dates in their local timezone, so validate against local date
        # The frontend handles timezone conversion for storage
        if result_date > date.today():
            raise ValueError('Transaction date cannot be in the future')

        return result_date


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


class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction."""
    stock_symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    transaction_type: Optional[TransactionType] = None
    quantity: Optional[Decimal] = Field(None, ge=0)
    price_per_share: Optional[Decimal] = Field(None, ge=0)
    fees: Optional[Decimal] = Field(None, ge=0)
    transaction_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('transaction_date')
    def validate_transaction_date(cls, v):
        # Users work in local timezone, validate against local date
        if v and v > date.today():
            raise ValueError('Transaction date cannot be in the future')
        return v


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list responses."""
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
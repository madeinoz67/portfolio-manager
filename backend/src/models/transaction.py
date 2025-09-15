"""
Transaction model for buy/sell activities.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from src.utils.datetime_utils import now

from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .portfolio import Portfolio
    from .stock import Stock


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    STOCK_SPLIT = "STOCK_SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    SPIN_OFF = "SPIN_OFF"
    MERGER = "MERGER"
    BONUS_SHARES = "BONUS_SHARES"


class SourceType(str, Enum):
    EMAIL = "EMAIL"
    MANUAL = "MANUAL"
    API = "API"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(Uuid, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(Uuid, ForeignKey("stocks.id"), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    price_per_share = Column(Numeric(10, 4), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    fees = Column(Numeric(10, 2), default=Decimal("0.00"))
    transaction_date = Column(DateTime, nullable=False)
    processed_date = Column(DateTime, default=now)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_reference = Column(String(255))
    broker_reference = Column(String(255))
    notes = Column(Text)
    is_verified = Column(Boolean, default=False)

    # Relationships
    portfolio: "Portfolio" = relationship("Portfolio", back_populates="transactions")
    stock: "Stock" = relationship("Stock", back_populates="transactions")

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, portfolio_id={self.portfolio_id}, "
            f"stock_id={self.stock_id}, type={self.transaction_type}, "
            f"quantity={self.quantity}, price={self.price_per_share})>"
        )
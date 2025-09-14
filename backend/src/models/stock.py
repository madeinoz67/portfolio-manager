"""
Stock model for tradeable securities master data.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from src.utils.datetime_utils import now

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Numeric, String, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .holding import Holding
    from .news_notice import NewsNotice
    from .price_history import PriceHistory
    from .transaction import Transaction


class StockStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    exchange = Column(String(50), nullable=False, default="ASX")
    current_price = Column(Numeric(10, 4))
    previous_close = Column(Numeric(10, 4))
    daily_change = Column(Numeric(8, 4))
    daily_change_percent = Column(Numeric(5, 2))
    status = Column(SQLEnum(StockStatus), default=StockStatus.ACTIVE)
    last_price_update = Column(DateTime)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    # Relationships
    holdings: list["Holding"] = relationship(
        "Holding", back_populates="stock", cascade="all, delete-orphan"
    )
    transactions: list["Transaction"] = relationship(
        "Transaction", back_populates="stock", cascade="all, delete-orphan"
    )
    price_history: list["PriceHistory"] = relationship(
        "PriceHistory", back_populates="stock", cascade="all, delete-orphan"
    )
    news_notices: list["NewsNotice"] = relationship(
        "NewsNotice", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Stock(id={self.id}, symbol='{self.symbol}', company_name='{self.company_name}')>"

    @property
    def volume(self) -> Optional[int]:
        """Get latest trading volume from most recent price history."""
        if self.price_history:
            latest = max(self.price_history, key=lambda p: p.price_date)
            return latest.volume
        return None
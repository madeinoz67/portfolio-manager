"""
Price history model for historical stock price data.
"""

import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .stock import Stock


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    stock_id = Column(Uuid, ForeignKey("stocks.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    open_price = Column(Numeric(10, 4))
    high_price = Column(Numeric(10, 4))
    low_price = Column(Numeric(10, 4))
    close_price = Column(Numeric(10, 4), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock: "Stock" = relationship("Stock", back_populates="price_history")

    # Composite unique constraint
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<PriceHistory(id={self.id}, stock_id={self.stock_id}, "
            f"date={self.price_date}, close={self.close_price})>"
        )
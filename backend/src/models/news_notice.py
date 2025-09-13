"""
News and Notices model for stock-related announcements and documents.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from src.database import Base

if TYPE_CHECKING:
    from .stock import Stock


class NewsNoticeType(str, Enum):
    NEWS = "NEWS"
    EARNINGS = "EARNINGS"
    DIVIDEND = "DIVIDEND"
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    REGULATORY_FILING = "REGULATORY_FILING"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    ANALYST_REPORT = "ANALYST_REPORT"
    PRESS_RELEASE = "PRESS_RELEASE"


class NewsNotice(Base):
    __tablename__ = "news_notices"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    stock_id = Column(Uuid, ForeignKey("stocks.id"), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    notice_type = Column(SQLEnum(NewsNoticeType), nullable=False)
    published_date = Column(DateTime, nullable=False)
    source = Column(String(200), nullable=True)
    external_url = Column(String(1000), nullable=True)
    document_url = Column(String(1000), nullable=True)  # Link to paperless document
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock: "Stock" = relationship("Stock", back_populates="news_notices")

    def __repr__(self) -> str:
        return f"<NewsNotice(id={self.id}, stock_id={self.stock_id}, title='{self.title}', type={self.notice_type})>"
"""
News and Notices schemas for serialization and validation.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from src.models.news_notice import NewsNoticeType


class NewsNoticeBase(BaseModel):
    """Base news notice schema with common fields."""
    title: str = Field(..., description="News/notice title")
    summary: Optional[str] = Field(None, description="Brief summary of the news/notice")
    content: Optional[str] = Field(None, description="Full content of the news/notice")
    notice_type: NewsNoticeType = Field(..., description="Type of news or notice")
    published_date: datetime = Field(..., description="When the news/notice was published")
    source: Optional[str] = Field(None, description="Source of the news/notice")
    external_url: Optional[str] = Field(None, description="External link for more information")
    document_url: Optional[str] = Field(None, description="Link to related document")


class NewsNoticeResponse(NewsNoticeBase):
    """Response schema for news notice data."""
    id: UUID = Field(..., description="Unique news notice identifier")
    stock_id: UUID = Field(..., description="Stock identifier")
    created_at: datetime = Field(..., description="When the record was created")
    updated_at: datetime = Field(..., description="When the record was last updated")

    model_config = {"from_attributes": True}


class NewsNoticeCreate(NewsNoticeBase):
    """Schema for creating a new news notice."""
    stock_id: UUID = Field(..., description="Stock identifier")


class NewsNoticeUpdate(BaseModel):
    """Schema for updating a news notice."""
    title: Optional[str] = Field(None, description="News/notice title")
    summary: Optional[str] = Field(None, description="Brief summary of the news/notice")
    content: Optional[str] = Field(None, description="Full content of the news/notice")
    notice_type: Optional[NewsNoticeType] = Field(None, description="Type of news or notice")
    published_date: Optional[datetime] = Field(None, description="When the news/notice was published")
    source: Optional[str] = Field(None, description="Source of the news/notice")
    external_url: Optional[str] = Field(None, description="External link for more information")
    document_url: Optional[str] = Field(None, description="Link to related document")
"""
Pydantic schemas for API key management.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: Optional[dict] = None


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)."""
    id: str
    name: str
    permissions: Optional[dict] = None
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes the actual key)."""
    id: str
    name: str
    key: str  # Only shown once during creation
    permissions: Optional[dict] = None
    expires_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
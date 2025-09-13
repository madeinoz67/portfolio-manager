"""
Pydantic schemas for API key management.
"""

from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, validator


class ApiKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: Optional[dict] = None
    expires_at: datetime = Field(..., description="Expiry date is required for security")

    @validator('expires_at')
    def validate_expiry_date(cls, v):
        """Validate expiry date for security requirements."""
        # Ensure both dates are timezone-naive for comparison
        now = datetime.utcnow()
        if hasattr(v, 'tzinfo') and v.tzinfo is not None:
            # Convert timezone-aware datetime to UTC then make naive
            v = v.utctimetuple()
            v = datetime(*v[:6])
        
        if v <= now:
            raise ValueError('Expiry date must be in the future for security')
        
        # Maximum expiry of 2 years for security
        max_expiry = now + timedelta(days=730)
        if v > max_expiry:
            raise ValueError('Maximum expiry period is 2 years for security')
        
        return v


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)."""
    id: str
    name: str
    permissions: Optional[dict] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        import json
        # Convert UUID to string and handle permissions JSON
        data = {
            'id': str(obj.id),
            'name': obj.name,
            'permissions': json.loads(obj.permissions) if obj.permissions else None,
            'last_used_at': obj.last_used_at,
            'expires_at': obj.expires_at,
            'is_active': obj.is_active,
            'created_at': obj.created_at
        }
        return cls(**data)


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes the actual key)."""
    id: str
    name: str
    key: str  # Only shown once during creation
    permissions: Optional[dict] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
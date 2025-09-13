"""
API Key management endpoints.
"""

import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.dependencies import get_current_active_user
from src.core.api_keys import generate_api_key, hash_api_key
from src.core.logging import get_logger
from src.database import get_db
from src.models.api_key import ApiKey
from src.models.user import User
from src.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user."""
    api_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active.is_(True)
    ).all()
    
    logger.info(f"User {current_user.email} retrieved {len(api_keys)} API keys")
    return [ApiKeyResponse.from_orm(api_key) for api_key in api_keys]


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user."""
    try:
        # Generate the API key
        plain_key = generate_api_key()
        key_hash = hash_api_key(plain_key)
        
        import json
        # Create the API key record
        api_key = ApiKey(
            user_id=current_user.id,
            name=api_key_data.name,
            key_hash=key_hash,
            permissions=json.dumps(api_key_data.permissions) if api_key_data.permissions else None,
            expires_at=api_key_data.expires_at,
            created_at=datetime.utcnow()
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"API key '{api_key_data.name}' created for user {current_user.email}")
        
        # Return the response with the plain key (only shown once)
        return ApiKeyCreateResponse(
            id=str(api_key.id),
            name=api_key.name,
            key=plain_key,
            permissions=api_key.permissions,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            created_at=api_key.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create API key for user {current_user.email}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    try:
        # Convert string ID to UUID
        try:
            key_uuid = uuid.UUID(api_key_id) if isinstance(api_key_id, str) else api_key_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API key ID format"
            )
        
        # Find the API key
        api_key = db.query(ApiKey).filter(
            ApiKey.id == key_uuid,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active.is_(True)
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Soft delete by setting is_active to False
        api_key.is_active = False
        db.commit()
        
        logger.info(f"API key '{api_key.name}' deleted for user {current_user.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"API key deletion failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key deletion failed"
        )


@router.patch("/{api_key_id}")
async def update_api_key(
    api_key_id: str,
    api_key_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an API key (name only)."""
    # Find the API key
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id,
        ApiKey.is_active.is_(True)
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Only allow updating the name
    if "name" in api_key_data:
        old_name = api_key.name
        api_key.name = api_key_data["name"]
        db.commit()
        
        logger.info(f"API key renamed from '{old_name}' to '{api_key.name}' for user {current_user.email}")
    
    return {"message": "API key updated successfully"}
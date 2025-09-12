"""
Authentication API endpoints for user registration and login.
"""

import json
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from src.core.dependencies import get_current_active_user
from src.core.logging import get_logger
from src.database import get_db
from src.core.api_keys import generate_api_key, hash_api_key
from src.models.user import User
from src.models.api_key import ApiKey
from src.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse
from src.schemas.auth import (
    UserLogin,
    UserRegister,
    TokenResponse,
    UserResponse,
    UserUpdate
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.
    """
    logger.info(f"User registration attempt for email: {user_data.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
        
        return UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            is_active=new_user.is_active,
            created_at=new_user.created_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return access token.
    """
    logger.info(f"Login attempt for email: {user_credentials.email}")
    
    # Get user from database
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user:
        logger.warning(f"Login failed - user not found: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Login failed - user inactive: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.password_hash):
        logger.warning(f"Login failed - invalid password: {user_credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    try:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User login successful: {user.email} (ID: {user.id})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )
        
    except Exception as e:
        logger.error(f"Token creation failed for user {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# User profile endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user's profile information.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile information.
    """
    try:
        # Update user fields
        if user_update.first_name is not None:
            current_user.first_name = user_update.first_name
            
        if user_update.last_name is not None:
            current_user.last_name = user_update.last_name
            
        if user_update.email_config is not None:
            # Convert dict to JSON string for storage
            import json
            current_user.email_config = json.dumps(user_update.email_config)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User profile updated: {current_user.email}")
        
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            is_active=current_user.is_active,
            created_at=current_user.created_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"User profile update failed for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


# API Key Management endpoints
@router.get("/me/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[ApiKeyResponse]:
    """
    List current user's API keys.
    """
    api_keys = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active.is_(True)
    ).all()
    
    return [
        ApiKeyResponse(
            id=str(key.id),
            name=key.name,
            permissions=json.loads(key.permissions) if key.permissions else None,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            is_active=key.is_active,
            created_at=key.created_at.isoformat()
        ) for key in api_keys
    ]


@router.post("/me/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ApiKeyCreateResponse:
    """
    Create a new API key for the current user.
    The key value is only shown once and cannot be retrieved later.
    """
    try:
        # Generate new API key
        api_key_value = generate_api_key()
        key_hash = hash_api_key(api_key_value)
        
        # Create API key record
        new_api_key = ApiKey(
            user_id=current_user.id,
            name=key_data.name,
            key_hash=key_hash,
            permissions=json.dumps(key_data.permissions) if key_data.permissions else None
        )
        
        db.add(new_api_key)
        db.commit()
        db.refresh(new_api_key)
        
        logger.info(f"API key created for user {current_user.email}: {key_data.name}")
        
        return ApiKeyCreateResponse(
            id=str(new_api_key.id),
            name=new_api_key.name,
            key=api_key_value,  # Only shown once!
            permissions=json.loads(new_api_key.permissions) if new_api_key.permissions else None,
            expires_at=new_api_key.expires_at.isoformat() if new_api_key.expires_at else None,
            created_at=new_api_key.created_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"API key creation failed for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key creation failed"
        )


@router.delete("/me/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) an API key.
    """
    try:
        # Find the API key
        api_key = db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active.is_(True)
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Deactivate the key (soft delete)
        api_key.is_active = False
        db.commit()
        
        logger.info(f"API key deactivated for user {current_user.email}: {api_key.name}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"API key deletion failed for {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key deletion failed"
        )
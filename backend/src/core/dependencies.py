"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.api_keys import get_user_by_api_key
from src.core.auth import verify_token, get_current_user_email
from src.core.logging import get_logger
from src.database import get_db
from src.models.user import User

logger = get_logger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract and verify token
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            logger.warning("Invalid JWT token provided")
            raise credentials_exception
        
        user_email = payload.get("sub")
        if user_email is None:
            logger.warning("JWT token missing user email")
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.email == user_email).first()
        if user is None:
            logger.warning(f"User not found for email: {user_email}")
            raise credentials_exception
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        logger.debug(f"User authenticated: {user_email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (redundant check for clarity).
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    return current_user


# Optional authentication - returns None if no token provided
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        user_email = payload.get("sub")
        if user_email is None:
            return None
        
        user = db.query(User).filter(User.email == user_email).first()
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.debug(f"Optional authentication failed: {e}")
        return None


# API Key authentication
async def get_user_by_api_key_header(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user by API key from X-API-Key header.
    Returns None if no API key provided or invalid.
    Raises HTTPException for expired keys.
    """
    if not x_api_key:
        return None
    
    from src.models.api_key import ApiKey
    from src.core.api_keys import hash_api_key
    from datetime import datetime
    
    # Check if the API key is expired specifically
    key_hash = hash_api_key(x_api_key)
    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active.is_(True)
    ).first()
    
    if api_key_record and api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    
    return get_user_by_api_key(db, x_api_key)


# Combined authentication: JWT or API Key
async def get_current_user_flexible(
    jwt_user: Optional[User] = Depends(get_current_user_optional),
    api_key_user: Optional[User] = Depends(get_user_by_api_key_header)
) -> User:
    """
    Get current user using either JWT token or API key.
    Prioritizes JWT token if both are provided.
    """
    user = jwt_user or api_key_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer, X-API-Key"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user
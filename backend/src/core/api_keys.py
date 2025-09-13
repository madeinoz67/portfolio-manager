"""
API key utilities for generating, hashing, and validating API keys.
"""

import secrets
import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.models.api_key import ApiKey
from src.models.user import User

logger = get_logger(__name__)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    Format: pk_<32_random_chars>
    """
    random_chars = secrets.token_urlsafe(24)  # ~32 chars when base64 encoded
    return f"pk_{random_chars}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    try:
        return hash_api_key(plain_key) == hashed_key
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        return False


def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    """
    Get user by API key.
    Returns None if key is invalid, expired, or inactive.
    """
    try:
        key_hash = hash_api_key(api_key)
        
        # Find the API key record
        api_key_record = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active.is_(True)
        ).first()
        
        if not api_key_record:
            logger.warning(f"Invalid API key attempted")
            return None
        
        # Check if expired
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key attempted: {api_key_record.name}")
            return None
        
        # Update last used timestamp
        api_key_record.last_used_at = datetime.utcnow()
        db.commit()
        
        # Get the user
        user = db.query(User).filter(
            User.id == api_key_record.user_id,
            User.is_active.is_(True)
        ).first()
        
        if not user:
            logger.warning(f"API key belongs to inactive user: {api_key_record.user_id}")
            return None
        
        logger.debug(f"API key authentication successful for user: {user.email}")
        return user
        
    except Exception as e:
        logger.error(f"API key authentication error: {e}")
        return None
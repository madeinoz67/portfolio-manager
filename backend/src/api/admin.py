"""
Admin API endpoints for user management and system administration.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.dependencies import get_current_admin_user, get_db
from src.core.logging import get_logger
from src.models.user import User
from src.schemas.auth import UserResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    List all users in the system.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting user list")

    users = db.query(User).all()

    return [
        UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get details of a specific user.
    Admin access required.
    """
    logger.info(f"Admin user {admin_user.email} requesting details for user {user_id}")

    from fastapi import HTTPException, status

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat()
    )
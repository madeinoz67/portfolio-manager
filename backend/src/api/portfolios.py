"""
Portfolio API endpoints.
"""

from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.dependencies import get_current_active_user, get_current_user_flexible
from src.database import get_db
from src.models import Portfolio, Holding, User, Stock, NewsNotice
from src.schemas.portfolio import (
    PortfolioCreate,
    PortfolioDeleteConfirmation,
    PortfolioResponse,
    PortfolioUpdate,
)
from src.schemas.holding import HoldingResponse
from src.schemas.news_notice import NewsNoticeResponse
from src.services.dynamic_portfolio_service import DynamicPortfolioService
from src.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/portfolios", tags=["Portfolios"])


@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> list[PortfolioResponse]:
    """List current user's portfolios."""
    portfolios = db.query(Portfolio).filter(
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).all()

    # Temporarily disable dynamic values to fix immediate issue
    return [PortfolioResponse.model_validate(p) for p in portfolios]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> PortfolioResponse:
    """Create new portfolio for the current user."""
    portfolio = Portfolio(
        name=portfolio_data.name,
        description=portfolio_data.description,
        owner_id=current_user.id
    )

    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    # Audit logging
    try:
        audit_service = AuditService(db)
        audit_service.log_portfolio_created(
            portfolio=portfolio,
            user_id=current_user.id,
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        db.commit()  # Commit audit log
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for portfolio creation: {e}")

    return PortfolioResponse.model_validate(portfolio)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> PortfolioResponse:
    """Get portfolio details for current user."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Temporarily use static values to fix immediate issue
    return PortfolioResponse.model_validate(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_data: PortfolioUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> PortfolioResponse:
    """Update portfolio for current user."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Capture changes for audit log
    changes = {}
    for field, value in portfolio_data.model_dump(exclude_unset=True).items():
        old_value = getattr(portfolio, field)
        if old_value != value:
            changes[field] = {"old": old_value, "new": value}
        setattr(portfolio, field, value)

    db.commit()
    db.refresh(portfolio)

    # Audit logging (only if there were actual changes)
    if changes:
        try:
            audit_service = AuditService(db)
            audit_service.log_portfolio_updated(
                portfolio=portfolio,
                user_id=current_user.id,
                changes=changes,
                ip_address=getattr(request.client, 'host', None) if request.client else None,
                user_agent=request.headers.get('User-Agent')
            )
            db.commit()  # Commit audit log
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create audit log for portfolio update: {e}")

    return PortfolioResponse.model_validate(portfolio)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> None:
    """Delete portfolio (soft delete) for current user."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Soft delete
    portfolio.is_active = False
    db.commit()


@router.post("/{portfolio_id}/delete", status_code=status.HTTP_200_OK)
async def delete_portfolio_with_confirmation(
    portfolio_id: UUID,
    confirmation: PortfolioDeleteConfirmation,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> dict:
    """Delete portfolio (soft delete) with name confirmation."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Verify confirmation name matches exactly
    if confirmation.confirmation_name != portfolio.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation name does not match portfolio name"
        )

    # Store portfolio name before deletion for audit log
    portfolio_name = portfolio.name

    # Soft delete
    portfolio.is_active = False
    db.commit()

    # Audit logging
    try:
        audit_service = AuditService(db)
        audit_service.log_portfolio_deleted(
            portfolio_id=str(portfolio_id),
            portfolio_name=portfolio_name,
            user_id=current_user.id,
            is_hard_delete=False,
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        db.commit()  # Commit audit log
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for portfolio deletion: {e}")

    return {"message": "Portfolio deleted successfully"}


@router.post("/{portfolio_id}/hard-delete", status_code=status.HTTP_200_OK)
async def hard_delete_portfolio_with_confirmation(
    portfolio_id: UUID,
    confirmation: PortfolioDeleteConfirmation,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_flexible)]
) -> dict:
    """Permanently delete portfolio and all related data with name confirmation."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.owner_id == current_user.id,
        Portfolio.is_active.is_(True)
    ).first()

    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )

    # Verify confirmation name matches exactly
    if confirmation.confirmation_name != portfolio.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation name does not match portfolio name"
        )

    # Store portfolio name before deletion for audit log
    portfolio_name = portfolio.name

    # Create audit log before deletion (since portfolio will be deleted)
    try:
        audit_service = AuditService(db)
        audit_service.log_portfolio_deleted(
            portfolio_id=str(portfolio_id),
            portfolio_name=portfolio_name,
            user_id=current_user.id,
            is_hard_delete=True,
            ip_address=getattr(request.client, 'host', None) if request.client else None,
            user_agent=request.headers.get('User-Agent')
        )
        # Don't commit yet - we'll commit after the deletion
    except Exception as e:
        # Log error but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log for portfolio hard deletion: {e}")

    # Hard delete - cascade will handle holdings and transactions
    db.delete(portfolio)
    db.commit()  # Commit both deletion and audit log

    return {"message": "Portfolio permanently deleted"}


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingResponse])
async def get_portfolio_holdings(
    portfolio_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> list[HoldingResponse]:
    """Get portfolio holdings."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.is_active.is_(True)
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Get holdings with recent news counts
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    holdings = db.query(Holding).join(Stock).filter(Holding.portfolio_id == portfolio_id).all()
    
    # Calculate recent news count for each holding
    holdings_with_news_count = []
    for holding in holdings:
        recent_news_count = db.query(func.count(NewsNotice.id)).filter(
            NewsNotice.stock_id == holding.stock_id,
            NewsNotice.published_date >= thirty_days_ago
        ).scalar() or 0
        
        # Convert to dict and add recent news count
        holding_dict = HoldingResponse.model_validate(holding).model_dump()
        holding_dict['recent_news_count'] = recent_news_count
        holdings_with_news_count.append(HoldingResponse.model_validate(holding_dict))
    
    return holdings_with_news_count


@router.get("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def get_holding_detail(
    portfolio_id: UUID,
    holding_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> HoldingResponse:
    """Get specific holding details."""
    holding = db.query(Holding).join(Stock).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.id == holding_id
    ).first()
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    return HoldingResponse.model_validate(holding)


@router.get("/{portfolio_id}/holdings/{holding_id}/news", response_model=list[NewsNoticeResponse])
async def get_holding_news_notices(
    portfolio_id: UUID,
    holding_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> list[NewsNoticeResponse]:
    """Get news and notices for a specific holding."""
    # First verify the holding exists in this portfolio
    holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.id == holding_id
    ).first()
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    # Get news and notices for the stock in this holding
    news_notices = db.query(NewsNotice).filter(
        NewsNotice.stock_id == holding.stock_id
    ).order_by(NewsNotice.published_date.desc()).all()
    
    return [NewsNoticeResponse.model_validate(notice) for notice in news_notices]
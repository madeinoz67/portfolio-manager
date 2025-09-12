"""
Portfolio API endpoints.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.dependencies import get_current_active_user, get_current_user_flexible
from src.database import get_db
from src.models import Portfolio, Holding, User
from src.schemas.portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
)

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
    return [PortfolioResponse.model_validate(p) for p in portfolios]


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
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
    
    return PortfolioResponse.model_validate(portfolio)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    portfolio_data: PortfolioUpdate,
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
    
    # Update fields that were provided
    for field, value in portfolio_data.model_dump(exclude_unset=True).items():
        setattr(portfolio, field, value)
    
    db.commit()
    db.refresh(portfolio)
    
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


@router.get("/{portfolio_id}/holdings")
async def get_portfolio_holdings(
    portfolio_id: UUID,
    db: Annotated[Session, Depends(get_db)]
) -> list:
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
    
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    
    # For now, return empty list until we implement holding schema
    return []
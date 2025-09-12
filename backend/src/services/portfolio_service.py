"""
Portfolio business logic service.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from src.core.exceptions import PortfolioNotFoundError
from src.core.logging import LoggerMixin
from src.models import Portfolio
from src.schemas.portfolio import PortfolioCreate, PortfolioResponse


class PortfolioService(LoggerMixin):
    """Service class for portfolio business logic."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_portfolios(self) -> List[PortfolioResponse]:
        """Get all active portfolios."""
        self.log_info("Fetching all active portfolios")
        
        portfolios = (
            self.db.query(Portfolio)
            .filter(Portfolio.is_active.is_(True))
            .all()
        )
        
        self.log_info("Retrieved portfolios", count=len(portfolios))
        return [PortfolioResponse.model_validate(p) for p in portfolios]
    
    def get_portfolio_by_id(self, portfolio_id: UUID) -> PortfolioResponse:
        """Get a portfolio by ID."""
        self.log_info("Fetching portfolio", portfolio_id=str(portfolio_id))
        
        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active.is_(True)
            )
            .first()
        )
        
        if not portfolio:
            self.log_warning("Portfolio not found", portfolio_id=str(portfolio_id))
            raise PortfolioNotFoundError(str(portfolio_id))
        
        self.log_info("Portfolio retrieved successfully", portfolio_id=str(portfolio_id))
        return PortfolioResponse.model_validate(portfolio)
    
    def create_portfolio(self, portfolio_data: PortfolioCreate) -> PortfolioResponse:
        """Create a new portfolio."""
        self.log_info("Creating new portfolio", name=portfolio_data.name)
        
        # Generate dummy owner ID for now (will be replaced with auth)
        owner_id = uuid4()
        
        portfolio = Portfolio(
            name=portfolio_data.name,
            description=portfolio_data.description,
            owner_id=owner_id
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        self.log_info("Portfolio created successfully", 
                     portfolio_id=str(portfolio.id), 
                     name=portfolio.name)
        
        return PortfolioResponse.model_validate(portfolio)
    
    def update_portfolio(
        self, 
        portfolio_id: UUID, 
        portfolio_data: PortfolioCreate
    ) -> PortfolioResponse:
        """Update an existing portfolio."""
        self.log_info("Updating portfolio", portfolio_id=str(portfolio_id))
        
        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active.is_(True)
            )
            .first()
        )
        
        if not portfolio:
            self.log_warning("Portfolio not found for update", portfolio_id=str(portfolio_id))
            raise PortfolioNotFoundError(str(portfolio_id))
        
        # Update fields
        portfolio.name = portfolio_data.name
        if portfolio_data.description is not None:
            portfolio.description = portfolio_data.description
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        self.log_info("Portfolio updated successfully", 
                     portfolio_id=str(portfolio_id),
                     name=portfolio.name)
        
        return PortfolioResponse.model_validate(portfolio)
    
    def delete_portfolio(self, portfolio_id: UUID) -> None:
        """Soft delete a portfolio."""
        self.log_info("Deleting portfolio", portfolio_id=str(portfolio_id))
        
        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == portfolio_id,
                Portfolio.is_active.is_(True)
            )
            .first()
        )
        
        if not portfolio:
            self.log_warning("Portfolio not found for deletion", portfolio_id=str(portfolio_id))
            raise PortfolioNotFoundError(str(portfolio_id))
        
        # Soft delete
        portfolio.is_active = False
        self.db.commit()
        
        self.log_info("Portfolio deleted successfully", portfolio_id=str(portfolio_id))
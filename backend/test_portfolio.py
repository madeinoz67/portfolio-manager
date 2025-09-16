#!/usr/bin/env python3

from src.database import SessionLocal
from src.models import Portfolio, Holding, Stock
from src.services.dynamic_portfolio_service import DynamicPortfolioService

db = SessionLocal()
try:
    # Get first portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.is_active == True).first()
    if portfolio:
        print(f'Portfolio found: {portfolio.name} (ID: {portfolio.id})')

        # Test dynamic portfolio service
        service = DynamicPortfolioService(db)
        dynamic_portfolio = service.get_dynamic_portfolio(portfolio.id)

        if dynamic_portfolio:
            print(f'Daily change: ${dynamic_portfolio.daily_change}')
            print(f'Daily change %: {dynamic_portfolio.daily_change_percent}%')
            print(f'Total value: ${dynamic_portfolio.total_value}')
        else:
            print('No dynamic portfolio data returned')

        # Check holdings
        holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        print(f'Holdings count: {len(holdings)}')
        for holding in holdings:
            print(f'- {holding.stock.symbol}: {holding.quantity} shares @ ${holding.average_cost}')
    else:
        print('No portfolios found')
finally:
    db.close()
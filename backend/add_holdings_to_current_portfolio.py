#!/usr/bin/env python3
"""
Script to add dummy holdings and transactions to the current demo user's portfolio.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import get_db, engine
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.stock import Stock
from src.models.holding import Holding
from src.models.transaction import Transaction
from sqlalchemy.orm import Session


def add_holdings_to_demo_portfolio():
    """Add dummy stocks, holdings, and transactions to demo user's portfolio."""
    
    db = Session(engine)
    
    try:
        # Get the demo user
        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            print("❌ Demo user not found. Please create demo@example.com first.")
            return
            
        # Get the specific portfolio ID
        target_portfolio_id = "d8b822f7-b9b0-4085-9ba8-18c12e0e7f5a"
        portfolio_uuid = uuid.UUID(target_portfolio_id)
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_uuid).first()
        if not portfolio:
            print(f"❌ Portfolio with ID {target_portfolio_id} not found.")
            return
            
        print(f"✅ Found portfolio: {portfolio.name} (ID: {portfolio.id})")
        
        # Create dummy stocks (same as before)
        stocks_data = [
            {"symbol": "AAPL", "company_name": "Apple Inc.", "current_price": "175.84"},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc.", "current_price": "127.33"},
            {"symbol": "MSFT", "company_name": "Microsoft Corporation", "current_price": "378.85"},
            {"symbol": "TSLA", "company_name": "Tesla, Inc.", "current_price": "248.50"},
            {"symbol": "AMZN", "company_name": "Amazon.com, Inc.", "current_price": "145.86"},
        ]
        
        stocks = []
        for stock_data in stocks_data:
            # Check if stock already exists
            existing_stock = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
            if existing_stock:
                print(f"📈 Stock {stock_data['symbol']} already exists")
                stocks.append(existing_stock)
            else:
                stock = Stock(
                    id=uuid.uuid4(),
                    symbol=stock_data["symbol"],
                    company_name=stock_data["company_name"],
                    current_price=stock_data["current_price"]
                )
                db.add(stock)
                stocks.append(stock)
                print(f"📈 Created stock: {stock_data['symbol']} - {stock_data['company_name']}")
        
        db.commit()
        
        # Create dummy holdings for the demo portfolio
        holdings_data = [
            {"stock": stocks[0], "quantity": "100", "average_cost": "150.00"},  # AAPL
            {"stock": stocks[1], "quantity": "50", "average_cost": "120.00"},   # GOOGL  
            {"stock": stocks[2], "quantity": "25", "average_cost": "350.00"},   # MSFT
            {"stock": stocks[3], "quantity": "75", "average_cost": "200.00"},   # TSLA
            {"stock": stocks[4], "quantity": "40", "average_cost": "130.00"},   # AMZN
        ]
        
        for holding_data in holdings_data:
            # Check if holding already exists for this portfolio
            existing_holding = db.query(Holding).filter(
                Holding.portfolio_id == portfolio.id,
                Holding.stock_id == holding_data["stock"].id
            ).first()
            
            if existing_holding:
                print(f"💼 Holding for {holding_data['stock'].symbol} already exists in this portfolio")
                continue
                
            quantity = float(holding_data["quantity"])
            avg_cost = float(holding_data["average_cost"])
            current_price = float(holding_data["stock"].current_price)
            
            current_value = quantity * current_price
            total_cost = quantity * avg_cost
            total_gain_loss = current_value - total_cost
            percentage_gain_loss = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
            
            holding = Holding(
                id=uuid.uuid4(),
                portfolio_id=portfolio.id,
                stock_id=holding_data["stock"].id,
                quantity=holding_data["quantity"],
                average_cost=holding_data["average_cost"],
                current_value=str(current_value),
                unrealized_gain_loss=str(total_gain_loss),
                unrealized_gain_loss_percent=str(percentage_gain_loss)
            )
            
            db.add(holding)
            print(f"💼 Created holding: {holding_data['stock'].symbol} - {quantity} shares @ ${avg_cost}")
        
        # Create dummy transactions for the demo portfolio
        base_date = datetime.now() - timedelta(days=30)
        
        transactions_data = [
            {"stock": stocks[0], "type": "BUY", "quantity": "50", "price": "145.00", "date_offset": 30},
            {"stock": stocks[0], "type": "BUY", "quantity": "50", "price": "155.00", "date_offset": 20},
            {"stock": stocks[1], "type": "BUY", "quantity": "50", "price": "120.00", "date_offset": 25},
            {"stock": stocks[2], "type": "BUY", "quantity": "25", "price": "350.00", "date_offset": 15},
            {"stock": stocks[3], "type": "BUY", "quantity": "100", "price": "180.00", "date_offset": 35},
            {"stock": stocks[3], "type": "SELL", "quantity": "25", "price": "220.00", "date_offset": 10},
            {"stock": stocks[4], "type": "BUY", "quantity": "40", "price": "130.00", "date_offset": 18},
        ]
        
        for trans_data in transactions_data:
            quantity = float(trans_data["quantity"])
            price = float(trans_data["price"])
            total_amount = quantity * price
            fees = total_amount * 0.001  # 0.1% fee
            
            transaction = Transaction(
                id=uuid.uuid4(),
                portfolio_id=portfolio.id,
                stock_id=trans_data["stock"].id,
                transaction_type=trans_data["type"],
                quantity=trans_data["quantity"],
                price_per_share=trans_data["price"],
                total_amount=str(total_amount),
                fees=str(fees),
                transaction_date=base_date + timedelta(days=trans_data["date_offset"]),
                notes=f"Dummy {trans_data['type'].lower()} transaction for testing",
                source_type="MANUAL"  # Required field
            )
            
            db.add(transaction)
            print(f"📊 Created transaction: {trans_data['type']} {quantity} {trans_data['stock'].symbol} @ ${price}")
        
        db.commit()
        
        # Update portfolio total value
        total_value = sum(
            float(h["quantity"]) * float(h["stock"].current_price) 
            for h in holdings_data
        )
        
        portfolio.total_value = str(total_value)
        portfolio.daily_change = "1250.75"  # Dummy daily change
        portfolio.daily_change_percent = "1.85"  # Dummy percentage
        
        db.commit()
        
        print(f"\n✅ Successfully added dummy data to demo user's portfolio!")
        print(f"   📈 Created {len(stocks)} stocks")
        print(f"   💼 Created {len(holdings_data)} holdings")
        print(f"   📊 Created {len(transactions_data)} transactions")
        print(f"   💰 Portfolio total value: ${total_value:,.2f}")
        print(f"\nYou can now view the portfolio detail page to see the formatted data!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding dummy data: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Adding dummy holdings and transactions to demo portfolio...")
    add_holdings_to_demo_portfolio()
    print("✅ Done!")
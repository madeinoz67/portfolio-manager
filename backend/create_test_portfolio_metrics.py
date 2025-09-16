#!/usr/bin/env python3
"""
Standalone script to create test portfolio metrics data for admin dashboard visibility.
This script puts data directly into the main database so it's visible in the admin dashboard.
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Add the backend src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db, Base, engine
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.stock import Stock
from src.models.holding import Holding
from src.models.portfolio_update_metrics import PortfolioUpdateMetric
from src.services.portfolio_update_metrics import PortfolioUpdateMetricsService
from src.core.auth import get_password_hash
from src.utils.datetime_utils import now


def create_test_data():
    """Create test data for portfolio metrics visibility."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Get database session
    db = next(get_db())

    try:
        print("🚀 Creating test portfolio metrics data...")

        # Create or get test user
        test_user = db.query(User).filter(User.email == "metrics-test@example.com").first()
        if not test_user:
            test_user = User(
                email="metrics-test@example.com",
                first_name="Metrics",
                last_name="Test",
                password_hash=get_password_hash("testpassword")
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.email}")

        # Create or get test portfolio
        test_portfolio = db.query(Portfolio).filter(
            Portfolio.owner_id == test_user.id,
            Portfolio.name == "Test Portfolio for Metrics"
        ).first()

        if not test_portfolio:
            test_portfolio = Portfolio(
                id=uuid.uuid4(),
                name="Test Portfolio for Metrics",
                description="Portfolio for testing admin dashboard metrics visibility",
                owner_id=test_user.id,
                total_value=Decimal("50000.00")
            )
            db.add(test_portfolio)
            db.commit()
            db.refresh(test_portfolio)
            print(f"✅ Created test portfolio: {test_portfolio.name}")

        # Create test stocks
        stock_data = [
            ("AAPL", "Apple Inc.", 185.00),
            ("GOOGL", "Alphabet Inc.", 140.50),
            ("TSLA", "Tesla Inc.", 248.75),
            ("MSFT", "Microsoft Corp.", 380.25),
            ("NVDA", "NVIDIA Corp.", 455.80)
        ]

        stocks = []
        for symbol, company_name, price in stock_data:
            existing_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not existing_stock:
                stock = Stock(
                    symbol=symbol,
                    company_name=company_name,
                    current_price=price,
                    exchange="NASDAQ",
                    last_price_update=now()
                )
                db.add(stock)
                stocks.append(stock)
            else:
                stocks.append(existing_stock)

        if stocks:
            db.commit()
            print(f"✅ Created/updated {len(stock_data)} test stocks")

        # Create portfolio metrics service
        metrics_service = PortfolioUpdateMetricsService(db)

        # Generate realistic portfolio update metrics
        base_time = now()
        update_scenarios = [
            # Recent successful updates (last hour)
            {
                "time_offset": timedelta(minutes=5),
                "symbols": ["AAPL", "GOOGL"],
                "duration": 120,
                "status": "success",
                "trigger": "market_data_change"
            },
            {
                "time_offset": timedelta(minutes=15),
                "symbols": ["TSLA"],
                "duration": 95,
                "status": "success",
                "trigger": "scheduled_update"
            },
            {
                "time_offset": timedelta(minutes=30),
                "symbols": ["MSFT", "NVDA"],
                "duration": 180,
                "status": "success",
                "trigger": "bulk_update"
            },
            {
                "time_offset": timedelta(minutes=45),
                "symbols": ["AAPL"],
                "duration": 75,
                "status": "success",
                "trigger": "market_data_change"
            },

            # Some updates from earlier today
            {
                "time_offset": timedelta(hours=2),
                "symbols": ["GOOGL", "TSLA"],
                "duration": 140,
                "status": "success",
                "trigger": "scheduled_update"
            },
            {
                "time_offset": timedelta(hours=4),
                "symbols": ["MSFT"],
                "duration": 200,
                "status": "warning",
                "trigger": "market_data_change"
            },
            {
                "time_offset": timedelta(hours=6),
                "symbols": ["NVDA", "AAPL"],
                "duration": 160,
                "status": "success",
                "trigger": "bulk_update"
            },

            # Historical data (yesterday)
            {
                "time_offset": timedelta(hours=12),
                "symbols": ["AAPL", "GOOGL", "TSLA"],
                "duration": 250,
                "status": "success",
                "trigger": "market_data_change"
            },
            {
                "time_offset": timedelta(hours=18),
                "symbols": ["MSFT", "NVDA"],
                "duration": 190,
                "status": "success",
                "trigger": "scheduled_update"
            },
            {
                "time_offset": timedelta(hours=20),
                "symbols": ["GOOGL"],
                "duration": 110,
                "status": "success",
                "trigger": "bulk_update"
            },

            # Some failures/errors for realistic data
            {
                "time_offset": timedelta(hours=8),
                "symbols": ["TSLA"],
                "duration": 300,
                "status": "error",
                "trigger": "market_data_change"
            },
            {
                "time_offset": timedelta(hours=14),
                "symbols": ["AAPL", "MSFT"],
                "duration": 250,
                "status": "warning",
                "trigger": "scheduled_update"
            }
        ]

        print(f"📊 Generating {len(update_scenarios)} portfolio update metrics...")

        metrics_created = 0
        for scenario in update_scenarios:
            recorded_at = base_time - scenario["time_offset"]

            try:
                metric = metrics_service.record_portfolio_update(
                    portfolio_id=str(test_portfolio.id),
                    symbols_updated=scenario["symbols"],
                    update_duration_ms=scenario["duration"],
                    status=scenario["status"],
                    trigger_type=scenario["trigger"],
                    update_source="test_data_generator",
                    created_at=recorded_at
                )
                metrics_created += 1
                print(f"  ✅ Created metric: {scenario['status']} update for {len(scenario['symbols'])} symbols")

            except Exception as e:
                print(f"  ❌ Failed to create metric: {e}")

        print(f"✅ Successfully created {metrics_created} portfolio update metrics")

        # Verify the data was created
        stats_24h = metrics_service.get_portfolio_update_stats_24h()
        performance_breakdown = metrics_service.get_portfolio_performance_breakdown(limit=10)

        print("\n📈 Metrics Summary:")
        print(f"  • Total updates (24h): {stats_24h['total_updates']}")
        print(f"  • Successful updates: {stats_24h['successful_updates']}")
        print(f"  • Success rate: {stats_24h['success_rate']:.1f}%")
        print(f"  • Avg duration: {stats_24h['avg_update_duration_ms']}ms")
        print(f"  • Unique portfolios: {stats_24h['unique_portfolios']}")
        print(f"  • Performance breakdown: {len(performance_breakdown)} portfolios")

        print(f"\n🎉 Portfolio metrics test data created successfully!")
        print(f"   You can now see the metrics in the admin dashboard at /admin/portfolio-metrics")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
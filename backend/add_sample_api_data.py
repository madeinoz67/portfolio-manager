#!/usr/bin/env python3
"""Add sample API usage data for testing admin dashboard."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db
from src.models.market_data_api_usage_metrics import ApiUsageMetrics
from datetime import datetime, timedelta
import random

def main():
    # Get database session
    db = next(get_db())

    # Create some realistic API usage records for the last few days
    providers = ['yfinance', 'alpha_vantage']
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META']

    print('Creating sample API usage data...')

    # Create data for last 7 days
    for day_offset in range(7):
        date = datetime.now() - timedelta(days=day_offset)

        for provider in providers:
            # Create realistic usage patterns
            if provider == 'yfinance':
                # yfinance gets more usage
                request_count = random.randint(5, 25) if day_offset < 3 else random.randint(0, 10)
                error_rate = 0.1  # 10% error rate
            else:
                # alpha_vantage gets minimal usage
                request_count = random.randint(0, 3) if day_offset < 5 else 0
                error_rate = 0.05  # 5% error rate

            # Create individual records (1 record = 1 API request)
            for _ in range(request_count):
                is_success = random.random() > error_rate
                record = ApiUsageMetrics(
                    provider_name=provider,
                    symbol=random.choice(symbols),
                    endpoint='/quote',
                    request_timestamp=date.replace(
                        hour=random.randint(8, 18),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    ),
                    response_status=200 if is_success else random.choice([429, 500, 503]),
                    success=is_success,
                    error_message=None if is_success else "Rate limit exceeded" if random.random() > 0.5 else "API timeout",
                    response_time_ms=random.randint(100, 2000),
                    rate_limit_remaining=random.randint(100, 500) if provider == 'alpha_vantage' else random.randint(1000, 2000)
                )
                db.add(record)

            if request_count > 0:
                success_count = int(request_count * (1 - error_rate))
                error_count = request_count - success_count
                print(f'Added {provider}: {request_count} requests ({success_count} success, {error_count} errors) on {date.date()}')

    db.commit()
    print('Sample data created successfully!')

    # Verify data
    total = db.query(ApiUsageMetrics).count()
    print(f'Total API usage records: {total}')

    # Show some statistics
    today_count = db.query(ApiUsageMetrics).filter(
        ApiUsageMetrics.request_timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    print(f'Today\'s records: {today_count}')

if __name__ == "__main__":
    main()
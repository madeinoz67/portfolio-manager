"""
Trend calculation service for price analysis.

Calculates price trends (up, down, neutral) and percentage changes
by comparing current prices to opening prices for each trading day.
"""

from enum import Enum
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from src.models.realtime_price_history import RealtimePriceHistory
from src.utils.datetime_utils import utc_now


logger = logging.getLogger(__name__)


class PriceTrend(Enum):
    """Price trend enumeration."""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


@dataclass
class TrendData:
    """Data structure for trend calculation results."""
    symbol: str
    current_price: Decimal
    opening_price: Decimal
    trend: PriceTrend
    change: Decimal
    change_percent: Decimal
    timestamp: datetime


class TrendCalculationService:
    """Service for calculating price trends and changes."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_trend(self, symbol: str) -> Optional[TrendData]:
        """Calculate trend for a single symbol."""
        latest_record = self._get_latest_price_record(symbol)

        if not latest_record:
            logger.debug(f"No price record available for {symbol}")
            return None

        current_price = latest_record.price

        # Use opening_price as primary, fallback to previous_close
        reference_price = latest_record.opening_price
        if reference_price is None:
            reference_price = latest_record.previous_close
            logger.debug(f"Using previous_close as fallback for {symbol} trend calculation")

        if reference_price is None:
            logger.debug(f"No opening price or previous_close available for {symbol}")
            return None

        # Calculate price change
        change = current_price - reference_price

        # Calculate percentage change
        change_percent = self._calculate_percentage_change(reference_price, current_price)

        # Determine trend
        if change > 0:
            trend = PriceTrend.UP
        elif change < 0:
            trend = PriceTrend.DOWN
        else:
            trend = PriceTrend.NEUTRAL

        return TrendData(
            symbol=symbol,
            current_price=current_price,
            opening_price=reference_price,  # Store the reference price used for calculation
            trend=trend,
            change=change,
            change_percent=change_percent,
            timestamp=latest_record.fetched_at
        )

    def calculate_trends(self, symbols: List[str]) -> List[TrendData]:
        """Calculate trends for multiple symbols."""
        trends = []

        for symbol in symbols:
            trend_data = self.calculate_trend(symbol)
            if trend_data:
                trends.append(trend_data)

        return trends

    def get_latest_opening_price(self, symbol: str) -> Optional[Decimal]:
        """Get the latest opening price for a symbol."""
        record = self._get_latest_price_record(symbol)
        return record.opening_price if record else None

    def get_latest_price(self, symbol: str) -> Optional[Decimal]:
        """Get the latest current price for a symbol."""
        record = self._get_latest_price_record(symbol)
        return record.price if record else None

    def _get_latest_price_record(self, symbol: str) -> Optional[RealtimePriceHistory]:
        """Get the latest price record for a symbol."""
        return self.db.query(RealtimePriceHistory)\
            .filter(RealtimePriceHistory.symbol == symbol)\
            .order_by(desc(RealtimePriceHistory.fetched_at))\
            .first()

    def _calculate_percentage_change(self, opening_price: Decimal, current_price: Decimal) -> Decimal:
        """Calculate percentage change with proper precision."""
        if opening_price == 0:
            return Decimal("0.00")

        change = current_price - opening_price
        percentage = (change / opening_price) * Decimal("100")

        # Round to 2 decimal places
        return percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_trend_summary(self, symbols: List[str]) -> Dict[str, int]:
        """Get summary of trends across multiple symbols."""
        trends = self.calculate_trends(symbols)

        summary = {
            "up": 0,
            "down": 0,
            "neutral": 0,
            "total": len(trends)
        }

        for trend_data in trends:
            summary[trend_data.trend.value] += 1

        return summary
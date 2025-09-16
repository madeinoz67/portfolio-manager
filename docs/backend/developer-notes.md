# Developer Notes - Portfolio P&L Improvements

## Current Task (Started: 2025-09-16)
**Objective**: Improve portfolio P&L reporting with clear unrealized vs daily calculations

### Requirements
1. **Unrealized P/L (Lifetime)**: Total unrealized profit/loss from purchase cost to current value
   - Show as $ amount and % change
   - This is the main P/L for portfolio's entire life
2. **Daily P/L**: Daily movement based on opening vs current prices
   - Show as $ amount and % change
   - Clearly labeled as "Daily" to avoid confusion
3. **Both displayed in**:
   - Portfolio summary view
   - Portfolio detail view
4. **Technical Requirements**:
   - Use TDD approach
   - Use Alembic for any schema changes
   - Commit often
   - Test all metrics to ensure no regressions
   - Clean, maintainable architecture

### Current Understanding
From previous work:
- Portfolio daily change calculation was fixed (src/services/dynamic_portfolio_service.py:179)
- Market data population service was implemented for previous close data
- Frontend currently shows both daily change (+$433.64) and total gain/loss (-$144.50)

### Architecture Decisions Needed
1. Field naming in API responses (clear labeling)
2. Database schema changes if needed for opening prices
3. Service layer updates for dual P/L calculations

### Next Steps
1. TDD research of current P/L calculations
2. Define clear field names and API structure
3. Implement lifetime unrealized P/L
4. Implement daily P/L with proper labeling
5. Update frontend views

### Files to Monitor for Regressions
- tests/test_portfolio_todays_change_bug_tdd.py
- tests/test_market_data_population_tdd.py
- tests/test_holdings_daily_change_display_tdd.py
- src/services/dynamic_portfolio_service.py
- Admin dashboard metrics

## Previous Work Summary
- Fixed daily change calculation bug (was incorrectly using total_unrealized_gain)
- Implemented market data population service for missing previous_close data
- All TDD tests passing for daily change calculations
- Frontend displays correct metrics but needs clearer labeling

## Questions for Clarification
- None at this time - requirements are clear
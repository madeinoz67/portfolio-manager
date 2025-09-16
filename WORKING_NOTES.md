# Working Notes - Single Master Symbol Table Implementation

## Current Task: Implementing Option C (Hybrid Master + History Reference)

**Status**: In progress - Creating Alembic migration for realtime_symbols master table

### Completed
✅ Design TDD test suite for single master symbol table
- Created comprehensive test suite in `tests/test_single_master_symbol_table_tdd.py`
- Defined expected behavior for realtime_symbols as single source of truth
- Tests cover schema validation, single-write patterns, API consistency
- Eliminates dual-table synchronization complexity

✅ Create Alembic migration for realtime_symbols master table
- Created migration 88b61f87b5c4 with SQLite-compatible schema
- realtime_symbols table with foreign keys to market_data_providers and realtime_price_history
- Primary key on symbol, indexes for performance
- Successfully applied to database

✅ Implement RealtimeSymbol model with history reference
- Created SQLAlchemy model in `src/models/realtime_symbol.py`
- Proper relationships to MarketDataProvider and RealtimePriceHistory
- Handle updated_at in application layer with update_timestamp() method
- Model imports successfully and ready for use

✅ Update market data service for single-write pattern
- Implemented store_price_to_master() method for Option C pattern
- Single-write to realtime_symbols with history reference
- Added get_current_price_from_master() for API consistency
- Both methods import successfully

### Implementation Complete ✅
✅ Migrate APIs to read from master table
- Updated DynamicPortfolioService to use RealtimeSymbol master table instead of RealtimePriceHistory
- Added get_current_price() method to PortfolioService for TDD test compliance
- Updated market data API endpoints (single price, bulk price, SSE streaming) to use get_current_price_from_master()
- Created AdminDashboardService with get_pricing_metrics() method using master table
- All APIs now read from single source of truth (realtime_symbols table)

### Next Steps
1. Implement RealtimeSymbol model with history reference
2. Update market data service for single-write pattern
3. Migrate APIs to read from master table
4. Update admin dashboard metrics to use master table
5. Run all tests and verify no regressions
6. Commit single master table implementation

### Key Architecture Changes
- **OLD**: Dual-table updates (stocks + realtime_price_history)
- **NEW**: Single master table (realtime_symbols) + history reference
- **Benefit**: Eliminates synchronization bugs, single source of truth

### Migration Requirements
- realtime_symbols table with current_price, last_updated, company_name
- latest_history_id foreign key to realtime_price_history
- Proper indexes for symbol lookups and timestamp queries
- Data migration from existing stocks table (if needed)

### User Requirements
- Use TDD approach throughout
- Use Alembic for database changes
- Follow debugging guidelines
- Commit often
- Mindful of admin dashboard metrics
- Ensure all tests passing
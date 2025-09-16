# Release Notes

This directory contains release notes for the Portfolio Manager application.

## Current Version

The application is currently in active development with the following major features implemented:

### Feature 003: Admin Dashboard ✅ COMPLETE
- **Branch**: `003-admin-dashboard`
- **Status**: Fully implemented with live activity tracking
- **Key Features**:
  - Admin user role management
  - Real-time system monitoring
  - Live activity feed with market data operations
  - User management capabilities
  - Market data provider configuration

### Feature 002: Market Data Integration (Planned)
- **Status**: Architecture designed, ready for implementation
- **Key Features**:
  - 15-minute interval market data updates
  - Server-Sent Events (SSE) for real-time UI updates
  - Alpha Vantage API integration (production)
  - yfinance integration (development)
  - Redis caching for performance

### Feature 001: Portfolio Performance Dashboard ✅ COMPLETE
- **Key Features**:
  - Portfolio creation and management
  - Stock holdings tracking
  - Performance analytics with P&L calculations
  - Real-time portfolio valuations
  - Responsive UI with dark/light themes

## Recent Fixes and Improvements

### Holdings Timestamp Fix (2025-09-16) ✅ RESOLVED
- **Issue**: Portfolio holdings displayed stale timestamps despite fresh market data
- **Solution**: Updated holdings endpoint to use RealtimeSymbol master table
- **Impact**: Portfolio holdings now display accurate timestamps

### Database Architecture Cleanup (2025-09-16) ✅ COMPLETE
- **Improvement**: Migrated to single master symbol table architecture
- **Removed**: Legacy price_history table and associated code
- **Result**: Cleaner, more efficient market data architecture

## Upcoming Releases

Release notes will be added here as new versions are deployed to production.

## Version Numbering

The application follows semantic versioning (SemVer) principles:
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible
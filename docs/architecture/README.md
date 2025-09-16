# Architecture Documentation

This directory contains technical architecture documentation, design decisions, and system implementation details for the Portfolio Manager application.

## Database Architecture

- [Database Schema Pricing](database-schema-pricing.md) - Pricing data schema and relationships
- [Single Master Symbol Table Architecture](single-master-symbol-table-architecture.md) - Master table design for market data
- [Price Fetching Architecture](price-fetching-architecture.md) - Market data fetching system design
- [Pricing Update Mechanisms](pricing-update-mechanisms.md) - How pricing data is updated and synchronized

## System Components

- [Scheduler API Architecture](scheduler-api-architecture.md) - Background task scheduling system
- [Metric Monitoring System](metric-monitoring-system.md) - Application metrics and monitoring
- [Queue Metrics Fix](queue-metrics-fix.md) - Portfolio update queue performance optimizations
- [Scheduler Metrics Singleton Fix](scheduler-metrics-singleton-fix.md) - Singleton pattern implementation for metrics

## Audit System

- [Audit System](audit-system.md) - Audit logging architecture and implementation
- [Audit Developer Guide](audit-developer-guide.md) - Technical guide for audit system development

## Frontend Architecture

- [Frontend Date Handling](frontend-date-handling.md) - Date/time handling patterns and timezone management
- [Frontend P&L Improvements](frontend-pl-improvements.md) - Profit & Loss calculation enhancements

## Issue Resolution & Troubleshooting

- [CSL Staleness Issue Resolution](csl-staleness-issue-resolution.md) - Resolution of market data staleness problems
- [Troubleshooting Pricing Issues](troubleshooting-pricing-issues.md) - Common pricing system issues and solutions

## Key Architectural Principles

1. **Single Source of Truth**: Use `realtime_symbols` as master table for all current market data
2. **Store Facts, Calculate Opinions**: Store transaction data, calculate current values dynamically
3. **Timezone Consistency**: Backend stores UTC, frontend converts to local time
4. **TDD Approach**: Test-driven development for all core functionality
5. **Performance Optimization**: Caching, queue-based processing, and efficient database queries
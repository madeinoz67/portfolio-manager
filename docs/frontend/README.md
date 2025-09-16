# Frontend Documentation

This directory contains frontend-specific documentation for the Portfolio Manager application.

## Frontend Guides

- [Frontend P&L Improvements](frontend-pl-improvements.md) - Profit & Loss calculation enhancements and UI improvements

## Frontend Architecture

The frontend is built with:
- **Next.js 15.5.3** with App Router
- **React 19.1.0** with TypeScript
- **Tailwind CSS** for styling
- **Server-Sent Events** for real-time updates
- **JWT Authentication** with role-based UI

## Key Features

### Real-time Updates
- Server-Sent Events (SSE) connection management
- Automatic reconnection with exponential backoff
- Connection status indicators (Live, Stale, Disconnected)

### Portfolio Management
- Multi-portfolio tracking with real-time valuations
- Interactive charts and performance analytics
- Responsive design for desktop and mobile

### Admin Dashboard
- System monitoring and user management
- Live activity feeds
- Market data provider configuration

## Development Guidelines

### Date/Time Handling
- Backend always sends UTC timestamps
- Frontend converts to local timezone using `Intl.DateTimeFormat`
- Use `formatDisplayDateTime` from `/utils/timezone.ts`
- Display dates as timestamps but show only date portion

### State Management
- React Context for auth and theme
- Custom hooks for market data streaming
- Local state for component-specific data

### API Integration
- RESTful API calls with proper error handling
- SSE streams for real-time data
- Automatic token refresh and logout

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Related Documentation

- [Developer](../developer/) - Development patterns and guidelines
- [Reference](../reference/) - API reference for frontend integration
- [User Guide](../user-guide/) - End-user features and functionality
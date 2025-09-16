# Portfolio Manager - Deployment Guide

This guide covers deploying the Portfolio Manager application with real-time market data capabilities to various environments.

## 🚀 Quick Start

### Development Environment

```bash
# Backend
cd backend
uv sync
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture Overview

- **Backend**: FastAPI with SQLAlchemy, real-time SSE streaming
- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis (optional, for performance)
- **Market Data**: Alpha Vantage API, yfinance fallback

## 🔧 Environment Configuration

### Backend Environment Variables

Create `.env` file in `backend/`:

```env
# Application
PM_APP_NAME="Portfolio Manager API"
PM_DEBUG=true
PM_HOST=0.0.0.0
PM_PORT=8001

# Security
PM_JWT_SECRET_KEY="your-super-secret-key-here"
PM_JWT_EXPIRE_MINUTES=10080

# Database (Development)
PM_DATABASE_URL="sqlite:///./portfolio_manager.db"

# Database (Production)
PM_DATABASE_URL="postgresql://user:pass@localhost:5432/portfolio_manager"
PM_DB_POSTGRES_USER="portfolio_user"
PM_DB_POSTGRES_PASSWORD="secure_password"
PM_DB_POSTGRES_DB="portfolio_manager"
PM_DB_POSTGRES_HOST="localhost"
PM_DB_POSTGRES_PORT=5432

# Market Data Providers
PM_ALPHA_VANTAGE_API_KEY="your-alpha-vantage-key"
PM_YFINANCE_ENABLED=true

# Cache (Optional)
PM_REDIS_URL="redis://localhost:6379/0"
PM_REDIS_HOST="localhost"
PM_REDIS_PORT=6379
PM_REDIS_DB=0

# CORS
PM_CORS_ORIGINS="http://localhost:3000,http://localhost:3001,https://yourdomain.com"

# Logging
PM_LOG_LEVEL="INFO"
PM_LOG_FORMAT="json"

# Monitoring (Optional)
PM_SENTRY_DSN="https://your-sentry-dsn"
```

### Frontend Environment Variables

Create `.env.local` file in `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
NODE_ENV=development
```

## 📊 Database Setup

### Development (SQLite)

```bash
cd backend
# Initialize database schema with Alembic (recommended)
uv run alembic upgrade head

# Alternative: Direct SQLAlchemy initialization
uv run python -c "
from src.database import engine, Base
from src.models import *
Base.metadata.create_all(bind=engine)
print('Database initialized!')
"
```

### Production (PostgreSQL)

1. **Install PostgreSQL**:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. **Create Database**:
```sql
CREATE USER portfolio_user WITH PASSWORD 'secure_password';
CREATE DATABASE portfolio_manager OWNER portfolio_user;
GRANT ALL PRIVILEGES ON DATABASE portfolio_manager TO portfolio_user;
```

3. **Initialize Schema**:
```bash
cd backend
export PM_DATABASE_URL="postgresql://portfolio_user:secure_password@localhost:5432/portfolio_manager"

# Initialize with Alembic migrations (recommended)
uv run alembic upgrade head

# Alternative: Direct SQLAlchemy initialization
uv run python -c "
from src.database import engine, Base
from src.models import *
Base.metadata.create_all(bind=engine)
print('Production database initialized!')
"
```

## 🔗 Market Data Configuration

### Alpha Vantage Setup

1. Register at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Get your free API key (500 requests/day)
3. Add to environment variables:
```env
PM_ALPHA_VANTAGE_API_KEY="YOUR_API_KEY_HERE"
```

### Rate Limiting Configuration

```env
PM_ALPHA_VANTAGE_RATE_LIMIT_PER_MINUTE=5
PM_ALPHA_VANTAGE_RATE_LIMIT_PER_DAY=500
PM_YFINANCE_RATE_LIMIT_PER_MINUTE=60
PM_DEFAULT_POLL_INTERVAL_MINUTES=15
```

## 🐳 Docker Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: portfolio_manager
      POSTGRES_USER: portfolio_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      PM_DATABASE_URL: postgresql://portfolio_user:secure_password@postgres:5432/portfolio_manager
      PM_REDIS_URL: redis://redis:6379/0
      PM_ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY}
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8001
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Start application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
```

## 🚀 Production Deployment

### 1. Server Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/portfolio-manager
sudo chown $USER:$USER /opt/portfolio-manager
cd /opt/portfolio-manager

# Clone repository
git clone https://github.com/yourusername/portfolio-manager.git .

# Setup backend
cd backend
uv sync
# Apply database migrations
uv run alembic upgrade head

# Setup frontend
cd ../frontend
npm install
npm run build
```

### 3. Process Management with systemd

Create `/etc/systemd/system/portfolio-backend.service`:

```ini
[Unit]
Description=Portfolio Manager Backend
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/portfolio-manager/backend
Environment=PATH=/opt/portfolio-manager/backend/.venv/bin
ExecStart=/opt/portfolio-manager/backend/.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8001 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/portfolio-frontend.service`:

```ini
[Unit]
Description=Portfolio Manager Frontend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/portfolio-manager/frontend
ExecStart=/usr/bin/npm start
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/portfolio-manager`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # SSE specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;
    }
}
```

### 5. SSL Setup

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/portfolio-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 6. Start Services

```bash
# Enable and start services
sudo systemctl enable portfolio-backend portfolio-frontend nginx postgresql redis
sudo systemctl start portfolio-backend portfolio-frontend
```

## 📊 Monitoring & Logging

### Application Logs

```bash
# Backend logs
sudo journalctl -u portfolio-backend -f

# Frontend logs
sudo journalctl -u portfolio-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

The backend provides health check endpoints:

- `GET /health` - Basic health status
- `GET /api/v1/market-data/status` - Market data service status

### Monitoring Script

Create `scripts/health-check.sh`:

```bash
#!/bin/bash

# Health check script
BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3000"

# Check backend
if curl -f "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is down"
    sudo systemctl restart portfolio-backend
fi

# Check frontend
if curl -f "$FRONTEND_URL" >/dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is down"
    sudo systemctl restart portfolio-frontend
fi
```

### Cron Job for Health Checks

```bash
# Add to crontab (crontab -e)
*/5 * * * * /opt/portfolio-manager/scripts/health-check.sh >> /var/log/portfolio-health.log 2>&1
```

## 🔐 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique JWT secrets
- Rotate API keys regularly

### Database Security
- Use strong passwords for database users
- Enable SSL connections for production databases
- Regular backups with encryption

### API Security
- Rate limiting is configured for market data endpoints
- JWT tokens expire after 7 days by default
- CORS origins should be restricted to your domain

### Server Security
- Keep system packages updated
- Use firewall to restrict access
- Monitor logs for suspicious activity
- Regular security audits

## 🔄 Maintenance

### Backup Strategy

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"

# Database backup
pg_dump portfolio_manager | gzip > "$BACKUP_DIR/portfolio_db_$DATE.sql.gz"

# Application backup
tar -czf "$BACKUP_DIR/portfolio_app_$DATE.tar.gz" /opt/portfolio-manager
```

### Update Process

```bash
# Pull latest code
cd /opt/portfolio-manager
git pull origin main

# Update backend
cd backend
uv sync
sudo systemctl restart portfolio-backend

# Update frontend
cd ../frontend
npm install
npm run build
sudo systemctl restart portfolio-frontend
```

## 🆘 Troubleshooting

### Common Issues

1. **SSE Connection Issues**
   - Check firewall settings
   - Verify proxy_buffering is off in Nginx
   - Check browser console for errors

2. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check connection string format
   - Ensure user permissions are correct

3. **Market Data Not Updating**
   - Verify API keys are set correctly
   - Check rate limiting logs
   - Ensure internet connectivity

4. **High CPU Usage**
   - Monitor active SSE connections
   - Check for infinite loops in price updates
   - Consider scaling with load balancer

### Log Analysis

```bash
# Find SSE connection issues
sudo journalctl -u portfolio-backend | grep -i "sse"

# Check market data errors
sudo journalctl -u portfolio-backend | grep -i "market.*data"

# Monitor database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE application_name LIKE 'portfolio%';"
```

## 📈 Performance Tuning

### Database Optimization

```sql
-- Create indexes for better performance

-- Single Master Symbol Table optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_realtime_symbols_last_updated
ON realtime_symbols(last_updated DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_realtime_symbols_provider
ON realtime_symbols(provider_id);

-- Historical data optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_realtime_prices_symbol_time
ON realtime_price_history(symbol, fetched_at DESC);

-- Portfolio performance optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_valuations_calc
ON portfolio_valuations(portfolio_id, calculated_at DESC);
```

### Redis Configuration

```
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

This deployment guide provides a comprehensive approach to deploying the Portfolio Manager with real-time market data capabilities across different environments.
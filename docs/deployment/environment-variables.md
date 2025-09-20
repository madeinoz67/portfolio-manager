# Environment Variables Documentation

## Overview

This document describes all environment variables used by the Portfolio Management System, with special focus on adapter configuration and security settings.

## Required Environment Variables

### Database Configuration

```bash
# Database connection
DATABASE_URL="postgresql://username:password@localhost:5432/portfolio_db"

# Alternative: Individual database settings
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="portfolio_db"
DB_USER="username"
DB_PASSWORD="password"
```

### Authentication & Security

```bash
# JWT token signing
SECRET_KEY="your-super-secret-key-here-min-32-chars"

# Encryption for sensitive adapter credentials
ENCRYPTION_KEY="base64-encoded-32-byte-encryption-key"

# CORS settings (optional)
FRONTEND_URL="http://localhost:3000"
```

### Market Data Adapter Secrets

#### Alpha Vantage
```bash
# API key from https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY="your_alpha_vantage_api_key"

# Optional: Custom settings
ALPHA_VANTAGE_TIMEOUT="30"
ALPHA_VANTAGE_RATE_LIMIT="5"  # requests per minute
```

#### IEX Cloud
```bash
# API token from https://iexcloud.io/
IEX_CLOUD_API_TOKEN="pk_your_publishable_token"

# For production use secret token
IEX_CLOUD_SECRET_TOKEN="sk_your_secret_token"

# Sandbox mode (for testing)
IEX_CLOUD_SANDBOX="false"
```

#### Polygon
```bash
# API key from https://polygon.io/
POLYGON_API_KEY="your_polygon_api_key"

# Subscription tier affects rate limits
POLYGON_TIER="basic"  # basic, starter, developer, advanced
```

#### Finnhub
```bash
# API key from https://finnhub.io/
FINNHUB_API_KEY="your_finnhub_api_key"
```

#### Yahoo Finance
```bash
# No API key required, but you can customize behavior
YAHOO_FINANCE_TIMEOUT="15"
YAHOO_FINANCE_USER_AGENT="PortfolioManager/1.0"
YAHOO_FINANCE_MAX_RETRIES="3"
```

## Optional Environment Variables

### Application Settings

```bash
# Environment
NODE_ENV="production"  # development, staging, production
DEBUG="false"

# Logging
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE="/var/log/portfolio/app.log"

# Server settings
HOST="0.0.0.0"
PORT="8000"
WORKERS="4"  # Number of worker processes
```

### Adapter System Configuration

```bash
# Health check intervals
ADAPTER_HEALTH_CHECK_INTERVAL="300"  # seconds (5 minutes)
ADAPTER_HEALTH_CHECK_TIMEOUT="30"   # seconds

# Metrics collection
METRICS_RETENTION_DAYS="90"
METRICS_AGGREGATION_INTERVAL="3600"  # seconds (1 hour)

# Performance settings
ADAPTER_DEFAULT_TIMEOUT="30"
ADAPTER_MAX_RETRIES="3"
ADAPTER_CIRCUIT_BREAKER_THRESHOLD="5"
```

### Cache and Performance

```bash
# Redis (if using for caching)
REDIS_URL="redis://localhost:6379/0"
REDIS_CACHE_TTL="1800"  # 30 minutes

# Request rate limiting
RATE_LIMIT_PER_MINUTE="60"
RATE_LIMIT_BURST="10"

# Background task settings
TASK_QUEUE_WORKERS="2"
TASK_RETRY_MAX="3"
```

### Monitoring and Alerting

```bash
# Prometheus metrics
PROMETHEUS_ENABLED="true"
PROMETHEUS_PORT="9090"

# Email notifications (optional)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
ALERT_EMAIL_FROM="alerts@yourcompany.com"
ALERT_EMAIL_TO="admin@yourcompany.com"

# Webhook notifications (optional)
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

## Development Environment

### .env File Example

Create a `.env` file in your project root:

```bash
# .env - Development environment variables

# Database
DATABASE_URL="sqlite:///./portfolio_dev.db"

# Security
SECRET_KEY="dev-secret-key-change-in-production-min-32-chars"
ENCRYPTION_KEY="ZGV2ZWxvcG1lbnQtZW5jcnlwdGlvbi1rZXktMzItYnl0ZXM="

# Debug mode
DEBUG="true"
LOG_LEVEL="DEBUG"

# Frontend URL
FRONTEND_URL="http://localhost:3000"

# Market data providers (development/testing)
ALPHA_VANTAGE_API_KEY="demo"  # Use demo key for testing
YAHOO_FINANCE_TIMEOUT="10"

# Disable production features in development
PROMETHEUS_ENABLED="false"
METRICS_AGGREGATION_INTERVAL="600"  # 10 minutes
```

### Docker Environment

For Docker deployments, create a `docker.env` file:

```bash
# docker.env - Docker environment variables

# Database (Docker Compose service)
DATABASE_URL="postgresql://portfolio:portfolio@db:5432/portfolio"

# Application
NODE_ENV="production"
SECRET_KEY="${SECRET_KEY}"
ENCRYPTION_KEY="${ENCRYPTION_KEY}"

# Market data
ALPHA_VANTAGE_API_KEY="${ALPHA_VANTAGE_API_KEY}"
IEX_CLOUD_API_TOKEN="${IEX_CLOUD_API_TOKEN}"

# Monitoring
PROMETHEUS_ENABLED="true"
METRICS_RETENTION_DAYS="30"
```

## Production Environment

### Secure Environment Variable Management

#### Using AWS Systems Manager Parameter Store

```bash
# Store secrets securely
aws ssm put-parameter \
  --name "/portfolio/production/alpha-vantage-api-key" \
  --value "your_actual_api_key" \
  --type "SecureString"

# Retrieve in application startup
ALPHA_VANTAGE_API_KEY=$(aws ssm get-parameter \
  --name "/portfolio/production/alpha-vantage-api-key" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text)
```

#### Using HashiCorp Vault

```bash
# Store secrets
vault kv put secret/portfolio/production \
  alpha_vantage_api_key="your_actual_api_key" \
  iex_cloud_token="your_actual_token"

# Retrieve in application
vault kv get -field=alpha_vantage_api_key secret/portfolio/production
```

#### Using Kubernetes Secrets

```yaml
# k8s-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: portfolio-secrets
type: Opaque
stringData:
  ALPHA_VANTAGE_API_KEY: "your_actual_api_key"
  IEX_CLOUD_API_TOKEN: "your_actual_token"
  SECRET_KEY: "your_actual_secret_key"
  ENCRYPTION_KEY: "your_actual_encryption_key"
```

### Environment Variable Validation

The application validates critical environment variables on startup:

```python
# Environment validation (automatic)
required_vars = [
    "DATABASE_URL",
    "SECRET_KEY",
    "ENCRYPTION_KEY",
]

optional_vars_with_defaults = {
    "LOG_LEVEL": "INFO",
    "ADAPTER_DEFAULT_TIMEOUT": "30",
    "METRICS_RETENTION_DAYS": "90",
}
```

## Security Best Practices

### API Key Management

1. **Never commit secrets to version control**
   ```bash
   # Add to .gitignore
   .env
   .env.local
   .env.production
   *.key
   ```

2. **Use different keys for different environments**
   ```bash
   # Development
   ALPHA_VANTAGE_API_KEY="demo_key_for_testing"

   # Production
   ALPHA_VANTAGE_API_KEY="prod_key_with_full_access"
   ```

3. **Rotate keys regularly**
   ```bash
   # Schedule key rotation
   0 0 1 * * /path/to/rotate-api-keys.sh
   ```

4. **Use least privilege principle**
   ```bash
   # IEX Cloud: Use publishable tokens when possible
   IEX_CLOUD_API_TOKEN="pk_..."  # Read-only access

   # Not: sk_... (secret tokens with write access)
   ```

### Encryption Key Generation

Generate secure encryption keys:

```bash
# Generate 32-byte encryption key
python -c "
import secrets
import base64
key = secrets.token_bytes(32)
print(base64.b64encode(key).decode())
"

# Or use OpenSSL
openssl rand -base64 32
```

### Secret Detection

Use tools to detect accidentally committed secrets:

```bash
# Install git-secrets
git secrets --install
git secrets --register-aws

# Scan for secrets
git secrets --scan

# Pre-commit hook
git secrets --install-hooks
```

## Troubleshooting

### Common Issues

#### "Missing API Key" Error
```bash
# Check if environment variable is set
echo $ALPHA_VANTAGE_API_KEY

# Check if it's being loaded
python -c "import os; print(os.getenv('ALPHA_VANTAGE_API_KEY'))"
```

#### "Encryption Key Invalid" Error
```bash
# Verify encryption key format
python -c "
import base64
import os
key = os.getenv('ENCRYPTION_KEY')
try:
    decoded = base64.b64decode(key)
    print(f'Key length: {len(decoded)} bytes')
    if len(decoded) == 32:
        print('✓ Valid encryption key')
    else:
        print('✗ Key must be 32 bytes')
except:
    print('✗ Invalid base64 encoding')
"
```

#### "Database Connection Failed" Error
```bash
# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
try:
    with engine.connect() as conn:
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
"
```

### Environment Variable Loading Order

The application loads environment variables in this order:

1. Operating system environment variables
2. `.env` file (if present)
3. Docker environment file (if using Docker)
4. Kubernetes secrets (if using K8s)
5. Cloud provider secret managers

Later sources override earlier ones.

### Debugging Environment Issues

Enable debug logging to see environment variable loading:

```bash
export DEBUG="true"
export LOG_LEVEL="DEBUG"

# Run application - you'll see detailed environment loading logs
python -m src.main
```

## Examples

### Local Development Setup

```bash
#!/bin/bash
# setup-dev-env.sh

echo "Setting up development environment..."

# Copy example environment file
cp .env.example .env

# Generate development keys
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")

# Update .env file
sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=${ENCRYPTION_KEY}/" .env

echo "Development environment configured!"
echo "Edit .env to add your API keys."
```

### Production Deployment Script

```bash
#!/bin/bash
# deploy-production.sh

echo "Deploying to production..."

# Validate required environment variables
required_vars=(
    "DATABASE_URL"
    "SECRET_KEY"
    "ENCRYPTION_KEY"
    "ALPHA_VANTAGE_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

echo "All required environment variables are set ✓"

# Deploy application
docker-compose -f docker-compose.prod.yml up -d

echo "Production deployment complete!"
```

---

*Keep this documentation updated as new environment variables are added to the system.*
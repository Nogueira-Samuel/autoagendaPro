# AutoAgenda Pro - Deployment Guide

Complete guide for deploying AutoAgenda Pro to production using Coolify or manual Docker deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment with Coolify (Recommended)](#deployment-with-coolify-recommended)
- [Manual Docker Deployment](#manual-docker-deployment)
- [Environment Variables](#environment-variables)
- [Supabase Configuration](#supabase-configuration)
- [Evolution API Setup](#evolution-api-setup)
- [Google Calendar Setup](#google-calendar-setup)
- [SSL/HTTPS Configuration](#sslhttps-configuration)
- [Monitoring and Logs](#monitoring-and-logs)
- [Backup Strategy](#backup-strategy)
- [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### Required Services

- **VPS/Server**:
  - Minimum: 2 vCPUs, 4GB RAM, 50GB SSD
  - Recommended: 4 vCPUs, 8GB RAM, 100GB SSD
  - OS: Ubuntu 22.04 LTS (recommended)

- **Domain Name**: For production deployment with SSL
- **Docker**: Version 20.10+ and Docker Compose v2+
- **PostgreSQL Database**: Supabase account (recommended) or self-hosted PostgreSQL 14+
- **Redis**: Version 7+ (optional but recommended)
- **Evolution API**: Self-hosted instance or managed service
- **Anthropic/OpenAI API Key**: For AI conversations
- **Google Cloud Project**: For Calendar API

### Required Accounts

1. **Supabase** (https://supabase.com) - Free tier available
2. **Anthropic** (https://console.anthropic.com) - API credits required
3. **OpenAI** (https://platform.openai.com) - Optional fallback
4. **Google Cloud Console** (https://console.cloud.google.com) - Free tier available

---

## Deployment with Coolify (Recommended)

Coolify is an open-source, self-hostable Heroku/Netlify alternative.

### Step 1: Install Coolify

```bash
# SSH into your VPS
ssh root@your-server-ip

# Install Coolify (one-line installer)
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Access Coolify at http://your-server-ip:8000
```

### Step 2: Initial Coolify Setup

1. Open `http://your-server-ip:8000` in browser
2. Create admin account
3. Configure server settings
4. Add your domain (optional)

### Step 3: Connect GitHub Repository

1. In Coolify dashboard, click **"New Resource"**
2. Select **"Public Repository"** or connect your GitHub account
3. Enter repository URL: `https://github.com/your-username/autoagendaPro`
4. Select branch: `main` or `production`
5. Set build pack: **Docker Compose**

### Step 4: Configure Build Settings

1. **Build Configuration**:
   - Build Pack: `Docker Compose`
   - Docker Compose Location: `/docker-compose.yml`
   - Dockerfile Location: `/backend/Dockerfile`

2. **Port Configuration**:
   - Container Port: `8000`
   - Publicly Exposed: `Yes`

3. **Health Check**:
   - Path: `/health`
   - Port: `8000`
   - Interval: `30s`

### Step 5: Configure Environment Variables

In Coolify, go to **Environment Variables** and add:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
API_SECRET_KEY=your-super-secret-key-change-this-min-32-chars

# Database (Supabase)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_MINUTES=43200

# AI Providers
ANTHROPIC_API_KEY=sk-ant-api03-xxx
OPENAI_API_KEY=sk-xxx

# WhatsApp (Evolution API)
EVOLUTION_API_URL=https://your-evolution-api.com
EVOLUTION_API_KEY=your-evolution-key
EVOLUTION_INSTANCE_NAME=autoagenda

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS={"type":"service_account","project_id":"..."}

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# CORS (update with your domain)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

### Step 6: Deploy

1. Click **"Deploy"** button
2. Monitor build logs in real-time
3. Wait for deployment to complete (2-5 minutes)

### Step 7: Run Database Migrations

After first deployment, run migrations:

```bash
# In Coolify, open terminal or SSH to server
docker exec -it autoagendapro-backend-1 alembic upgrade head

# Verify migration
docker exec -it autoagendapro-backend-1 alembic current
```

### Step 8: Configure Domain and SSL

1. In Coolify, go to **Domains**
2. Add your domain: `api.yourdomain.com`
3. Enable **"Generate Let's Encrypt Certificate"**
4. Update DNS records:
   ```
   Type: A
   Name: api
   Value: your-server-ip
   TTL: 3600
   ```
5. Wait for SSL certificate generation (2-10 minutes)

---

## Manual Docker Deployment

For deployment without Coolify.

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Repository

```bash
# Clone repository
git clone https://github.com/your-username/autoagendaPro.git
cd autoagendaPro

# Checkout production branch (if applicable)
git checkout main
```

### Step 3: Configure Environment

```bash
# Create environment file
cd backend
cp .env.example .env

# Edit environment variables
nano .env
```

Update with production values (see [Environment Variables](#environment-variables) section).

### Step 4: Build and Deploy

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f backend

# Check running containers
docker compose ps
```

### Step 5: Run Migrations

```bash
# Execute migrations
docker compose exec backend alembic upgrade head

# Verify
docker compose exec backend alembic current
```

### Step 6: Configure Nginx (Reverse Proxy)

```bash
# Install Nginx
sudo apt install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/autoagenda
```

Add configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/autoagenda /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: Configure SSL with Certbot

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## Environment Variables

Complete reference of all environment variables:

### Application Settings

```bash
# Environment mode (development, production)
ENVIRONMENT=production

# Enable debug mode (false for production)
DEBUG=false

# Secret key for JWT (generate with: openssl rand -hex 32)
API_SECRET_KEY=your-super-secret-key-min-32-characters

# API Title and Version
API_TITLE=AutoAgenda Pro API
API_VERSION=1.0.0
```

### Database Configuration

```bash
# PostgreSQL connection string
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# Connection pool settings (optional)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### JWT Configuration

```bash
# Access token expiration (minutes)
# Default: 10080 (7 days)
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Refresh token expiration (minutes)
# Default: 43200 (30 days)
REFRESH_TOKEN_EXPIRE_MINUTES=43200

# JWT algorithm
JWT_ALGORITHM=HS256
```

### AI Provider Configuration

```bash
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OpenAI GPT (fallback)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# Default LLM provider (anthropic or openai)
DEFAULT_LLM_PROVIDER=anthropic
```

### WhatsApp (Evolution API)

```bash
# Evolution API base URL
EVOLUTION_API_URL=https://evolution.yourdomain.com

# Evolution API key (global API key)
EVOLUTION_API_KEY=your-evolution-global-api-key

# Default instance name
EVOLUTION_INSTANCE_NAME=autoagenda

# Webhook URL (your API endpoint)
EVOLUTION_WEBHOOK_URL=https://api.yourdomain.com/api/v1/webhooks/whatsapp
```

### Google Calendar

```bash
# Service Account credentials (full JSON)
GOOGLE_CALENDAR_CREDENTIALS={"type":"service_account","project_id":"your-project","private_key_id":"xxx","private_key":"-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n","client_email":"autoagenda@your-project.iam.gserviceaccount.com","client_id":"xxx","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"xxx"}

# Default timezone
TIMEZONE=America/Sao_Paulo
```

### Redis Configuration

```bash
# Redis connection URL
# Format: redis://host:port/db
REDIS_URL=redis://localhost:6379/0

# Redis password (if required)
REDIS_PASSWORD=your-redis-password

# Enable Redis (true/false)
REDIS_ENABLED=true
```

### CORS Configuration

```bash
# Allowed origins (JSON array)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com","https://admin.yourdomain.com"]

# Allow credentials
CORS_ALLOW_CREDENTIALS=true
```

---

## Supabase Configuration

### Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Click **"New Project"**
3. Fill in details:
   - Name: `autoagenda-pro`
   - Database Password: (generate strong password)
   - Region: Choose closest to your users
   - Pricing Plan: Free or Pro

### Step 2: Get Connection String

1. In Supabase dashboard, go to **Settings → Database**
2. Copy **Connection String** (URI format)
3. Replace `[YOUR-PASSWORD]` with your database password
4. Add to `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres.xxx:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
   ```

### Step 3: Configure Connection Pooling

For production, use connection pooler:

```bash
# Use pooler connection string (port 6543)
DATABASE_URL=postgresql://postgres.xxx:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?pgbouncer=true
```

### Step 4: Run Initial Migrations

```bash
# From your server/local machine
cd backend
alembic upgrade head
```

### Step 5: Verify Database

1. In Supabase dashboard, go to **Table Editor**
2. Verify tables were created:
   - `tenants`
   - `users`
   - `customers`
   - `appointments`
   - `services`
   - `business_config`
   - `conversations`

---

## Evolution API Setup

### Option 1: Self-Hosted Evolution API

```bash
# Clone Evolution API
git clone https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api

# Configure
cp .env.example .env
nano .env

# Start with Docker
docker compose up -d

# Access at http://your-server:8080
```

### Option 2: Use Managed Service

Use a managed Evolution API provider (recommended for production).

### Configuration Steps

1. **Create Instance** via Evolution API Manager or API:
   ```bash
   curl -X POST https://evolution.yourdomain.com/instance/create \
     -H "apikey: YOUR-GLOBAL-API-KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "instanceName": "autoagenda",
       "token": "your-instance-token",
       "qrcode": true,
       "webhook": {
         "url": "https://api.yourdomain.com/api/v1/webhooks/whatsapp",
         "events": ["messages.upsert", "connection.update"]
       }
     }'
   ```

2. **Connect WhatsApp**:
   ```bash
   # Get QR Code
   curl https://evolution.yourdomain.com/instance/connect/autoagenda \
     -H "apikey: YOUR-GLOBAL-API-KEY"

   # Scan QR code with WhatsApp mobile app
   ```

3. **Verify Connection**:
   ```bash
   curl https://evolution.yourdomain.com/instance/connectionState/autoagenda \
     -H "apikey: YOUR-GLOBAL-API-KEY"
   ```

---

## Google Calendar Setup

### Step 1: Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **"Select a project" → "New Project"**
3. Name: `AutoAgenda Pro`
4. Click **"Create"**

### Step 2: Enable Calendar API

1. In the project, go to **"APIs & Services" → "Library"**
2. Search for **"Google Calendar API"**
3. Click **"Enable"**

### Step 3: Create Service Account

1. Go to **"APIs & Services" → "Credentials"**
2. Click **"Create Credentials" → "Service Account"**
3. Fill in:
   - Name: `autoagenda-calendar`
   - ID: `autoagenda-calendar`
   - Description: `Service account for AutoAgenda Pro`
4. Click **"Create and Continue"**
5. Skip optional steps, click **"Done"**

### Step 4: Generate JSON Key

1. Click on created service account
2. Go to **"Keys"** tab
3. Click **"Add Key" → "Create new key"**
4. Choose **JSON** format
5. Click **"Create"** (downloads JSON file)

### Step 5: Configure Service Account

1. Open downloaded JSON file
2. Copy entire content
3. Minify JSON (remove line breaks):
   ```bash
   # Use online tool or:
   cat service-account.json | jq -c
   ```
4. Add to `.env`:
   ```bash
   GOOGLE_CALENDAR_CREDENTIALS='{"type":"service_account",...}'
   ```

### Step 6: Share Calendars

For each client/tenant, they must share their Google Calendar with the service account email:

1. Open Google Calendar (https://calendar.google.com)
2. Click on calendar settings (gear icon next to calendar name)
3. Click **"Share with specific people"**
4. Add service account email: `autoagenda-calendar@your-project.iam.gserviceaccount.com`
5. Set permission: **"Make changes to events"**
6. Click **"Send"**

---

## SSL/HTTPS Configuration

### With Coolify

SSL is automatic with Coolify - just add your domain and enable Let's Encrypt.

### Manual Setup with Certbot

Already covered in [Manual Docker Deployment](#step-7-configure-ssl-with-certbot).

### SSL Best Practices

1. **Use Strong Ciphers**:
   ```nginx
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers HIGH:!aNULL:!MD5;
   ssl_prefer_server_ciphers on;
   ```

2. **Enable HSTS**:
   ```nginx
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   ```

3. **Configure SSL Session**:
   ```nginx
   ssl_session_cache shared:SSL:10m;
   ssl_session_timeout 10m;
   ```

---

## Monitoring and Logs

### Application Logs

**With Docker Compose**:
```bash
# View all logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# Save logs to file
docker compose logs backend > backend.log
```

**With Coolify**:
- Access logs directly in Coolify dashboard
- Real-time log streaming available
- Automatic log rotation

### Health Checks

```bash
# Check API health
curl https://api.yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### Monitoring Tools

**Recommended Tools**:
1. **UptimeRobot** - Free uptime monitoring
2. **Sentry** - Error tracking
3. **Grafana + Prometheus** - Advanced metrics
4. **PostgreSQL logs** - Query performance

**Setup Uptime Monitoring**:
```bash
# Add to UptimeRobot:
# URL: https://api.yourdomain.com/health
# Type: HTTP(s)
# Interval: 5 minutes
```

---

## Backup Strategy

### Database Backups

**Automated Supabase Backups**:
- Supabase Pro plan includes automatic daily backups
- Point-in-time recovery available
- Backups retained for 7 days (Pro) or 30 days (Team)

**Manual Backups**:
```bash
# Backup entire database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup specific tables
pg_dump $DATABASE_URL \
  -t tenants -t users -t appointments -t customers \
  > backup_main_tables_$(date +%Y%m%d).sql

# Compress backup
gzip backup_*.sql
```

**Automated Backup Script**:
```bash
#!/bin/bash
# save as backup.sh

BACKUP_DIR="/home/backups/autoagenda"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="autoagenda_backup_${DATE}.sql"

# Create backup
pg_dump $DATABASE_URL > ${BACKUP_DIR}/${FILENAME}

# Compress
gzip ${BACKUP_DIR}/${FILENAME}

# Delete backups older than 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${FILENAME}.gz"
```

**Schedule with Cron**:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/scripts/backup.sh >> /home/logs/backup.log 2>&1
```

### Environment Configuration Backup

```bash
# Backup .env file
cp .env .env.backup.$(date +%Y%m%d)

# Store securely (encrypted)
gpg -c .env.backup.$(date +%Y%m%d)
```

### Restore from Backup

```bash
# Decompress
gunzip backup_20240101_020000.sql.gz

# Restore
psql $DATABASE_URL < backup_20240101_020000.sql

# Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM tenants;"
```

---

## Post-Deployment Verification

### 1. API Health Check

```bash
curl https://api.yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

### 2. Database Connection

```bash
# Check Alembic migration status
docker compose exec backend alembic current

# Should show latest migration
```

### 3. Test Authentication

```bash
# Register test user
curl -X POST https://api.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "full_name": "Test User",
    "tenant_id": 1
  }'

# Login
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "tenant_id": 1
  }'
```

### 4. Test WhatsApp Webhook

```bash
# Send test message to Evolution API
curl -X POST https://evolution.yourdomain.com/message/sendText/autoagenda \
  -H "apikey: YOUR-API-KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5511999999999",
    "text": "Olá, teste do AutoAgenda Pro!"
  }'
```

### 5. Interactive API Documentation

Open in browser:
- Swagger UI: `https://api.yourdomain.com/docs`
- ReDoc: `https://api.yourdomain.com/redoc`

### 6. Monitoring Setup

1. Add health check to UptimeRobot
2. Configure error tracking (Sentry)
3. Set up log alerts
4. Create admin dashboard

---

## Troubleshooting Deployment

### API Not Starting

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Database connection - verify DATABASE_URL
# 2. Missing environment variables - check .env
# 3. Port conflict - change port in docker-compose.yml
```

### Database Migration Errors

```bash
# Check current migration
alembic current

# Show migration history
alembic history

# Force migration to specific version
alembic upgrade head --sql > migration.sql
# Review migration.sql before applying
```

### SSL Certificate Issues

```bash
# Check Nginx configuration
sudo nginx -t

# Renew certificate manually
sudo certbot renew

# Check certificate expiration
sudo certbot certificates
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check database connections
docker compose exec backend psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Optimize database
docker compose exec backend psql $DATABASE_URL -c "VACUUM ANALYZE;"
```

---

## Next Steps

After successful deployment:

1. **Configure First Tenant**: See [SETUP_CLIENTE.md](SETUP_CLIENTE.md)
2. **Test WhatsApp Integration**: Send test messages
3. **Configure Monitoring**: Set up alerts and monitoring
4. **Documentation**: Share API docs with team
5. **Backup Verification**: Test restore process

---

## Support and Resources

- **API Documentation**: `/docs` endpoint
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues**: For bug reports and feature requests

---

**Last Updated**: 2024
**Version**: 1.0.0

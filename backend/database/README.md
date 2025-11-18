# Database Setup and Migrations

Complete guide for database setup, migrations, and seeding for AutoAgenda Pro.

## Overview

AutoAgenda Pro uses:
- **Database**: PostgreSQL 14+ (via Supabase recommended)
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic with async support
- **Driver**: asyncpg for async PostgreSQL operations

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Running Migrations](#running-migrations)
- [Seeding Data](#seeding-data)
- [Common Commands](#common-commands)
- [Migration Best Practices](#migration-best-practices)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

1. **PostgreSQL Database**
   - PostgreSQL 14+ installed locally, or
   - Supabase project (recommended for production)

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   - Create `.env` file in `backend/` directory
   - Add database URL:
     ```bash
     DATABASE_URL=postgresql://user:password@host:5432/dbname
     ```

## Initial Setup

### 1. Configure Database Connection

Add to `backend/.env`:

```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# Or local PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/autoagenda
```

### 2. Verify Alembic Setup

The Alembic configuration is already set up. Verify it exists:

```bash
cd backend
ls alembic.ini  # Should exist
ls alembic/     # Should contain env.py and versions/
```

### 3. Create Initial Migration

Generate migration from your SQLAlchemy models:

```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
```

This creates a migration file in `alembic/versions/` with all table definitions.

### 4. Review Generated Migration

**IMPORTANT**: Always review auto-generated migrations before applying!

```bash
# Open the latest migration file
ls -t alembic/versions/*.py | head -1
```

Check for:
- ✓ All tables are included
- ✓ Foreign keys are correct
- ✓ Indexes are properly defined
- ✓ Enum types are created

### 5. Apply Migrations

Run the migration to create all tables:

```bash
alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
```

### 6. Verify Tables

Check that tables were created:

```sql
-- In psql or your database client
\dt  -- List all tables

-- Should show:
-- tenants
-- users
-- business_configs
-- services
-- customers
-- appointments
-- conversations
```

### 7. Seed Initial Data (Optional)

Populate database with test data:

```bash
cd backend
python -m database.seeds.initial_data
```

This creates:
- Test tenant: "Clínica Exemplo"
- Admin user: `admin@clinica-exemplo.com` / `admin123`
- Sample services: Consulta, Exame, Retorno
- Business configuration with default hours

## Running Migrations

### Check Current Version

```bash
alembic current
```

Output:
```
001 (head)
```

### View Migration History

```bash
alembic history --verbose
```

### Apply All Pending Migrations

```bash
# Apply all migrations
alembic upgrade head

# Apply next migration only
alembic upgrade +1

# Apply to specific revision
alembic upgrade abc123
```

### Rollback Migrations

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations
alembic downgrade base
```

### Create New Migration

After modifying models in `app/models/`:

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add column to users table"

# Create empty migration (manual)
alembic revision -m "Add custom index"
```

## Seeding Data

### Seed Development Data

```bash
cd backend
python -m database.seeds.initial_data
```

### Clear All Data (Development Only)

**⚠️ WARNING: This deletes ALL data!**

```bash
python -m database.seeds.initial_data --clear
```

You'll be prompted to confirm by typing `DELETE ALL DATA`.

### Create Custom Seed Script

Create new seed file in `database/seeds/`:

```python
# database/seeds/my_custom_data.py
import asyncio
from app.database import DatabaseManager
from app.models import MyModel

async def seed():
    session_factory = DatabaseManager.get_session_factory()
    async with session_factory() as db:
        # Add your data here
        item = MyModel(name="Test")
        db.add(item)
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed())
```

Run with:
```bash
python -m database.seeds.my_custom_data
```

## Common Commands

### Migration Commands

```bash
# Check current version
alembic current

# View history
alembic history

# Create migration (autogenerate)
alembic revision --autogenerate -m "Description"

# Create empty migration
alembic revision -m "Description"

# Apply migrations
alembic upgrade head        # All pending
alembic upgrade +1          # Next one
alembic upgrade abc123      # To specific

# Rollback migrations
alembic downgrade -1        # Last one
alembic downgrade abc123    # To specific
alembic downgrade base      # All

# Show SQL without executing
alembic upgrade head --sql

# Stamp database (mark as specific version without running)
alembic stamp head
```

### Database Commands

```bash
# Seed initial data
python -m database.seeds.initial_data

# Clear all data (destructive!)
python -m database.seeds.initial_data --clear

# Verify database connection
python -c "from app.database import DatabaseManager; print('✓ Connected')"
```

## Migration Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's autogenerate is smart but not perfect. Always check:

- ✓ Column types are correct
- ✓ Nullable constraints match your intent
- ✓ Indexes are created where needed
- ✓ Foreign keys are properly defined
- ✓ Enum types are handled correctly

### 2. Test Migrations in Development First

```bash
# In development
alembic upgrade head  # Apply
# Test your application
alembic downgrade -1  # Rollback
alembic upgrade head  # Apply again
```

### 3. Backup Production Database

**Before running migrations in production:**

```bash
# For PostgreSQL
pg_dump -h host -U user -d database > backup_$(date +%Y%m%d).sql

# For Supabase
# Use Supabase dashboard to create backup
```

### 4. Use Transactions

Migrations run in transactions by default. For complex migrations:

```python
def upgrade():
    # Alembic automatically wraps this in a transaction
    op.add_column('users', sa.Column('new_field', sa.String()))
    op.execute("UPDATE users SET new_field = 'default'")
```

### 5. Document Breaking Changes

If a migration requires application changes:

```python
"""Add required email field to users

**BREAKING CHANGE**: This migration adds a required `email` field.
Before deploying, ensure your application code is updated to:
1. Provide email during user creation
2. Handle missing emails for existing users

Revision ID: abc123
"""
```

### 6. Handle Data Migrations Carefully

For migrations that modify data:

```python
def upgrade():
    # Add column as nullable first
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))

    # Populate data
    op.execute("UPDATE users SET email = CONCAT(username, '@example.com')")

    # Make it required
    op.alter_column('users', 'email', nullable=False)
```

## Troubleshooting

### Issue: Import errors when running migrations

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
Ensure you're in the `backend/` directory:
```bash
cd backend
alembic upgrade head
```

### Issue: Database connection refused

**Error:**
```
sqlalchemy.exc.OperationalError: connection refused
```

**Solution:**
1. Check DATABASE_URL in `.env`
2. Verify PostgreSQL is running
3. Test connection:
   ```bash
   psql $DATABASE_URL
   ```

### Issue: Migrations out of sync

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solution:**
```bash
# Check current version
alembic current

# Check pending migrations
alembic history

# Force stamp to specific version (if you know what you're doing)
alembic stamp head
```

### Issue: Enum type already exists

**Error:**
```
DuplicateObject: type "user_role" already exists
```

**Solution:**
The migration tries to create an enum that already exists. Update migration:

```python
def upgrade():
    # Instead of:
    # op.execute("CREATE TYPE user_role AS ENUM (...)")

    # Use:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('admin', 'user');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
```

### Issue: Foreign key constraint fails

**Error:**
```
ForeignKeyViolation: insert or update violates foreign key constraint
```

**Solution:**
Ensure parent records exist before inserting child records in migrations.

## Production Deployment

### Initial Production Setup

```bash
# 1. Set production environment variables
export DATABASE_URL="postgresql://user:pass@prod-host:5432/db"
export ENVIRONMENT="production"

# 2. Run migrations (do NOT seed data)
cd backend
alembic upgrade head

# 3. Verify
alembic current  # Should show latest version

# 4. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Deploying New Migrations

```bash
# 1. Backup database first!
pg_dump ... > backup.sql

# 2. Pull latest code
git pull origin main

# 3. Check pending migrations
alembic current
alembic history

# 4. Apply migrations
alembic upgrade head

# 5. Restart application
# (method depends on your hosting)
```

### Rollback Plan

Always have a rollback plan:

```bash
# If migration fails or causes issues:

# 1. Rollback migration
alembic downgrade -1

# 2. Restore from backup (if needed)
psql $DATABASE_URL < backup.sql

# 3. Rollback application code
git checkout <previous-version>

# 4. Restart application
```

## Database Schema

Current schema includes:

### Core Tables

- **tenants** - Multi-tenant isolation
  - id, name, slug, plan, timezone
  - Google Calendar credentials
  - Evolution API settings

- **users** - System users with RBAC
  - id, tenant_id, email, password_hash
  - role (super_admin, admin, operator, viewer)

- **business_configs** - Business settings
  - tenant_id, business_hours (JSON)
  - Appointment settings
  - Message templates

- **services** - Services offered
  - id, tenant_id, name, description
  - duration_minutes, price, color

- **customers** - End customers
  - id, tenant_id, name, phone, email
  - WhatsApp integration

- **appointments** - Scheduled appointments
  - id, tenant_id, customer_id, service_id
  - scheduled_date, scheduled_time
  - status, google_calendar_event_id

- **conversations** - WhatsApp message history
  - id, tenant_id, customer_id
  - message, direction, type
  - timestamp, metadata

### Relationships

```
Tenant (1) ──→ (N) Users
Tenant (1) ──→ (1) BusinessConfig
Tenant (1) ──→ (N) Services
Tenant (1) ──→ (N) Customers
Tenant (1) ──→ (N) Appointments

Customer (1) ──→ (N) Appointments
Customer (1) ──→ (N) Conversations

Service (1) ──→ (N) Appointments
```

## Support

For issues or questions:

1. Check this README
2. Review Alembic logs
3. Check application logs (LOG_LEVEL=DEBUG)
4. Consult [Alembic documentation](https://alembic.sqlalchemy.org/)
5. Consult [SQLAlchemy documentation](https://docs.sqlalchemy.org/)

---

**Last Updated**: 2025-11-17
**Database Version**: PostgreSQL 14+
**ORM**: SQLAlchemy 2.0
**Migrations**: Alembic 1.13+

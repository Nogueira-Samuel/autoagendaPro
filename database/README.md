# 🗄️ Database Documentation

## Overview

AutoAgenda Pro uses PostgreSQL hosted on Supabase for data persistence. The database is accessed asynchronously using SQLAlchemy 2.0 with asyncpg driver.

## Database Schema

### Main Tables

#### Users
Stores user information and WhatsApp contact details.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    language VARCHAR(10) DEFAULT 'pt-BR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Appointments
Stores appointment information and Google Calendar integration.

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(500),
    google_calendar_event_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Conversations
Stores WhatsApp conversation history for AI context.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Conversation Sessions
Tracks conversation sessions for context management.

```sql
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);
```

## Supabase Setup

### 1. Create a Supabase Project

1. Go to [Supabase](https://supabase.com/)
2. Sign up or log in
3. Create a new project
4. Wait for the database to be provisioned

### 2. Get Database URL

1. Go to Project Settings → Database
2. Copy the connection string under "Connection string"
3. Format: `postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres`
4. Add this to your `.env` file as `DATABASE_URL`

### 3. Enable Required Extensions

Run these SQL commands in the Supabase SQL Editor:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### 4. Set Up Row Level Security (RLS)

Supabase has RLS enabled by default. For the backend to access tables:

```sql
-- Disable RLS for service role (backend uses service role key)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_sessions DISABLE ROW LEVEL SECURITY;
```

Alternatively, create appropriate RLS policies if you want more security.

## Database Migrations with Alembic

### Initialize Alembic

```bash
cd backend
alembic init alembic
```

### Create Migration

```bash
alembic revision --autogenerate -m "Create initial tables"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Downgrade to base
alembic downgrade base
```

### Migration Best Practices

1. Always review auto-generated migrations before applying
2. Test migrations on a development database first
3. Create backups before running migrations in production
4. Write both `upgrade()` and `downgrade()` functions
5. Use descriptive migration messages

## Database Models

Models are defined in `backend/app/models/` using SQLAlchemy ORM.

Example model structure:

```python
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255))
    timezone = Column(String(50), default="America/Sao_Paulo")
    language = Column(String(10), default="pt-BR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## Database Access Patterns

### Using Async Sessions

```python
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

### Transactions

```python
async with get_db() as session:
    try:
        # Multiple operations
        session.add(user)
        session.add(appointment)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
```

## Indexing Strategy

Key indexes for performance:

```sql
-- User lookups by phone
CREATE INDEX idx_users_phone ON users(phone_number);

-- Appointment queries by user and time
CREATE INDEX idx_appointments_user_time ON appointments(user_id, start_time);

-- Conversation history
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);

-- Active sessions
CREATE INDEX idx_sessions_active ON conversation_sessions(user_id, is_active) WHERE is_active = TRUE;
```

## Backup and Restore

### Backup

Supabase automatically creates daily backups. For manual backups:

```bash
pg_dump -h [HOST] -U postgres -d postgres > backup.sql
```

### Restore

```bash
psql -h [HOST] -U postgres -d postgres < backup.sql
```

## Performance Optimization

1. **Connection Pooling**: Configured in `database.py`
2. **Async Operations**: All database operations are async
3. **Indexes**: Strategic indexes on frequently queried columns
4. **Query Optimization**: Use `select_in_load` for relationships
5. **Caching**: Redis cache for frequently accessed data

## Monitoring

Use Supabase Dashboard to monitor:
- Active connections
- Query performance
- Storage usage
- Error logs

## Security Best Practices

1. **Use environment variables** for database credentials
2. **Never commit** database passwords to version control
3. **Use SSL connections** in production
4. **Implement RLS policies** for multi-tenant scenarios
5. **Regular backups** and disaster recovery plan
6. **Monitor for suspicious activity**

## Troubleshooting

### Connection Issues

```python
# Test database connection
from app.database import DatabaseManager

engine = DatabaseManager.get_engine()
async with engine.connect() as conn:
    result = await conn.execute(text("SELECT 1"))
    print(result.fetchone())
```

### Migration Conflicts

```bash
# View migration history
alembic history

# Stamp current version without running migrations
alembic stamp head
```

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

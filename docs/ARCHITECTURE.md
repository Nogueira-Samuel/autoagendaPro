# AutoAgenda Pro - System Architecture

Comprehensive architecture documentation for AutoAgenda Pro, an AI-powered WhatsApp appointment scheduling system.

## Table of Contents

- [System Overview](#system-overview)
- [High-Level Architecture](#high-level-architecture)
- [Technology Stack](#technology-stack)
- [Multi-Tenant Architecture](#multi-tenant-architecture)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [Security Architecture](#security-architecture)
- [Scalability](#scalability)
- [Performance](#performance)
- [Deployment Architecture](#deployment-architecture)

---

## System Overview

AutoAgenda Pro is a multi-tenant SaaS application that enables businesses to automate appointment scheduling through WhatsApp using AI-powered conversational interfaces.

### Key Capabilities

- **AI-Powered Conversations**: Natural language processing using Claude AI/GPT
- **WhatsApp Integration**: Bidirectional messaging via Evolution API
- **Calendar Sync**: Automatic Google Calendar event management
- **Multi-Tenant**: Complete data isolation between clients
- **Real-Time**: Async processing for instant responses
- **Scalable**: Designed for horizontal scaling

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     AutoAgenda Pro                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  FastAPI     │  │  SQLAlchemy  │  │  Alembic     │    │
│  │  Backend     │  │  ORM         │  │  Migrations  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Claude AI   │  │  Evolution   │  │  Google      │    │
│  │  / GPT       │  │  API         │  │  Calendar    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │  Redis       │  │  JWT Auth    │    │
│  │  (Supabase)  │  │  Cache       │  │  Security    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## High-Level Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          External Services                          │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │  WhatsApp    │   │  Anthropic   │   │  Google      │         │
│  │  Users       │   │  Claude API  │   │  Calendar    │         │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘         │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼───────────────────┐
│                       API Gateway Layer                            │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │  Evolution   │   │  REST API    │   │  Webhooks    │         │
│  │  API Client  │   │  Endpoints   │   │  Receiver    │         │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼───────────────────┐
│                     Application Layer                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              FastAPI Application                     │          │
│  │                                                      │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │          │
│  │  │ Routers  │  │ Services │  │ Middleware│         │          │
│  │  │          │  │          │  │           │         │          │
│  │  │ - Auth   │  │ - LLM    │  │ - Auth    │         │          │
│  │  │ - Appts  │  │ - WhatsApp│ │ - Tenant  │         │          │
│  │  │ - Cust   │  │ - Calendar│ │ - Logging │         │          │
│  │  └──────────┘  └──────────┘  └──────────┘         │          │
│  └─────────────────────────────────────────────────────┘          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              Business Logic Layer                    │          │
│  │                                                      │          │
│  │  ┌──────────────┐  ┌──────────────┐               │          │
│  │  │ Conversation │  │ Appointment  │               │          │
│  │  │ Manager      │  │ Scheduler    │               │          │
│  │  └──────────────┘  └──────────────┘               │          │
│  └─────────────────────────────────────────────────────┘          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                        Data Layer                                   │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │  PostgreSQL  │   │  Redis       │   │  SQLAlchemy  │         │
│  │  Database    │   │  Cache       │   │  ORM         │         │
│  │  (Supabase)  │   │              │   │              │         │
│  └──────────────┘   └──────────────┘   └──────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. WhatsApp User sends message
   │
   ▼
2. Evolution API receives message
   │
   ▼
3. Evolution API sends webhook to AutoAgenda Pro
   │
   ▼
4. Webhook Router receives and validates
   │
   ▼
5. ConversationManager processes message
   │
   ├─► LLM Service (Claude/GPT) analyzes intent
   │
   ├─► Database queries customer/business info
   │
   └─► Google Calendar checks availability
   │
   ▼
6. Action executed (create appointment, etc.)
   │
   ▼
7. Response generated by LLM
   │
   ▼
8. Response sent back via Evolution API
   │
   ▼
9. User receives response in WhatsApp
```

---

## Technology Stack

### Backend Framework

**FastAPI** (Python 3.11+)
- Async/await support
- Automatic OpenAPI documentation
- Pydantic validation
- High performance (Starlette + Uvicorn)

### Database

**PostgreSQL 14+** (via Supabase)
- ACID compliance
- JSON support for flexible data
- Full-text search
- Row-level security

**SQLAlchemy 2.0**
- Async ORM
- Type-safe queries
- Relationship management

**Alembic**
- Database migrations
- Version control
- Rollback support

### Caching

**Redis 7+**
- Session management
- Rate limiting
- Message queuing
- Caching layer

### AI/LLM

**Anthropic Claude 3.5**
- Portuguese language optimization
- Context-aware conversations
- Intent detection
- Entity extraction

**OpenAI GPT-4** (Alternative)
- Function calling
- Structured outputs
- Fallback provider

### External APIs

**Evolution API**
- WhatsApp multi-instance
- Message sending/receiving
- Media support
- Status updates

**Google Calendar API**
- Event CRUD operations
- Availability checking
- Service Account authentication

### Authentication & Security

**JWT** (JSON Web Tokens)
- Stateless authentication
- HS256 algorithm
- Refresh token support

**Bcrypt**
- Password hashing
- Cost factor 12
- Salt generation

### Development Tools

**Pydantic**
- Data validation
- Type hints
- Schema generation

**Python-Jose**
- JWT handling
- Cryptographic operations

**Asyncpg**
- PostgreSQL async driver
- Connection pooling

---

## Multi-Tenant Architecture

### Tenant Isolation

Each tenant (client business) has complete data isolation.

```
┌─────────────────────────────────────────────────┐
│              Database Schema                    │
│                                                 │
│  ┌────────────────────────────────────────┐   │
│  │           tenants                      │   │
│  │  - id (PK)                             │   │
│  │  - name                                │   │
│  │  - slug                                │   │
│  │  - plan (free/basic/premium)          │   │
│  └──┬─────────────────────────────────────┘   │
│     │                                          │
│     │ Foreign Key: tenant_id                   │
│     │                                          │
│  ┌──▼─────────┐  ┌──────────┐  ┌──────────┐  │
│  │   users    │  │ services │  │ customers│  │
│  └────────────┘  └──────────┘  └──────────┘  │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │business_ │  │appoint-  │  │conversa- │    │
│  │configs   │  │ments     │  │tions     │    │
│  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────┘
```

### Tenant Identification

Multiple methods supported:

1. **Query Parameter**: `?tenant_id=1`
2. **HTTP Header**: `X-Tenant-ID: 1`
3. **JWT Token**: Extracted from user's token
4. **Subdomain** (Future): `tenant1.autoagenda.com`

### Data Isolation

- All tables have `tenant_id` foreign key
- Database-level constraints prevent cross-tenant access
- Application-level validation in middleware
- Unique constraints scoped per tenant (e.g., email unique per tenant)

### Tenant-Specific Configuration

Each tenant has:
- Own Google Calendar credentials
- Own Evolution API instance
- Own business hours
- Own message templates
- Own timezone settings

---

## Data Flow

### WhatsApp Message Processing

```
┌─────────────────────────────────────────────────────────────┐
│  1. Message Received                                        │
│                                                             │
│     WhatsApp User → Evolution API → Webhook                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  2. Webhook Processing                                      │
│                                                             │
│     Extract: phone, message, instance_name                 │
│     Validate: tenant exists, active                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  3. Conversation Manager                                    │
│                                                             │
│     Get/Create Customer → Load Context → Process with LLM  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  4. LLM Processing                                          │
│                                                             │
│     Detect Intent → Extract Entities → Generate Response   │
│                                                             │
│     Intents: schedule, cancel, reschedule, info            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  5. Action Execution                                        │
│                                                             │
│     IF intent == schedule:                                  │
│        Check availability → Create appointment              │
│        → Create Google Calendar event                       │
│                                                             │
│     IF intent == cancel:                                    │
│        Cancel appointment → Delete Calendar event           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  6. Save Conversation                                       │
│                                                             │
│     Save to database: message, response, intent, metadata  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  7. Send Response                                           │
│                                                             │
│     Evolution API → WhatsApp User                          │
│     (with typing indicator for natural feel)               │
└─────────────────────────────────────────────────────────────┘
```

### Appointment Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. Creation                                                │
│     Source: WhatsApp / REST API                            │
│     → Validate customer, service, time                      │
│     → Check availability (Google Calendar)                  │
│     → Create appointment (status: pending)                  │
│     → Create Calendar event                                 │
│     → Send confirmation message                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  2. Confirmation                                            │
│     Auto-confirm (if enabled)                              │
│     OR Manual confirmation by admin                         │
│     → Update status: confirmed                              │
│     → Send reminder schedule                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  3. Reminders                                               │
│     24 hours before: Send reminder via WhatsApp            │
│     1 hour before: Send final reminder                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  4. Completion / Cancellation                               │
│                                                             │
│     IF completed:                                           │
│        Update status: completed                             │
│        Keep Calendar event for history                      │
│                                                             │
│     IF cancelled:                                           │
│        Update status: cancelled                             │
│        Delete Calendar event                                │
│        Save cancellation reason                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. FastAPI Application

**Location:** `backend/app/main.py`

**Responsibilities:**
- HTTP request handling
- Middleware pipeline
- Exception handling
- CORS configuration
- OpenAPI documentation

**Key Features:**
- Async request handling
- Lifespan events (startup/shutdown)
- Automatic validation (Pydantic)
- Dependency injection

### 2. Routers

**Location:** `backend/app/routers/`

**Modules:**
- `auth.py` - Authentication endpoints
- `appointments.py` - Appointment CRUD
- `customers.py` - Customer management
- `webhooks.py` - External webhooks

**Pattern:** Clean separation of concerns, thin controllers

### 3. Services

**Location:** `backend/app/services/`

**Modules:**
- `conversation_manager.py` - Orchestrates message processing
- `llm_factory.py` - LLM provider abstraction
- `claude_service.py` - Anthropic Claude integration
- `openai_service.py` - OpenAI GPT integration
- `google_calendar_service.py` - Calendar API wrapper
- `whatsapp_service.py` - Evolution API wrapper

**Pattern:** Service layer with dependency injection

### 4. Models

**Location:** `backend/app/models/`

**Tables:**
- `tenants` - Client businesses
- `users` - System users (RBAC)
- `business_configs` - Business settings
- `services` - Services offered
- `customers` - End customers
- `appointments` - Scheduled appointments
- `conversations` - Message history

**Pattern:** SQLAlchemy ORM with relationships

### 5. Utilities

**Location:** `backend/app/utils/`

**Modules:**
- `auth.py` - JWT & password hashing
- `security.py` - Security helpers
- `validators.py` - Custom validators (CPF, phone)
- `redis_client.py` - Cache abstraction
- `timezone_utils.py` - Timezone handling

---

## Security Architecture

### Authentication Flow

```
1. User Login
   ├─► Validate email/password
   ├─► Hash comparison (bcrypt)
   ├─► Generate access token (JWT)
   ├─► Generate refresh token (JWT)
   └─► Return tokens to client

2. Protected Request
   ├─► Extract token from Authorization header
   ├─► Verify signature (HS256)
   ├─► Check expiration
   ├─► Load user from database
   └─► Proceed with request

3. Token Refresh
   ├─► Validate refresh token
   ├─► Generate new access token
   └─► Return new token
```

### Security Measures

**1. Password Security**
- Bcrypt hashing (cost factor 12)
- Automatic salt generation
- Password strength validation

**2. Token Security**
- JWT with HS256 algorithm
- Short-lived access tokens (7 days)
- Refresh token rotation
- Secure secret key storage

**3. Input Validation**
- Pydantic schema validation
- XSS protection (input sanitization)
- SQL injection prevention (ORM)
- Brazilian phone/CPF validation

**4. API Security**
- HTTPS only (production)
- CORS configuration
- Rate limiting (100 req/min)
- Request logging

**5. Data Protection**
- Multi-tenant isolation
- Row-level security
- Sensitive data masking
- PII protection

---

## Scalability

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (e.g., Nginx)                         │
└────────┬────────────────┬────────────────┬─────────────┘
         │                │                │
┌────────▼────┐  ┌───────▼─────┐  ┌──────▼──────┐
│  FastAPI    │  │  FastAPI    │  │  FastAPI    │
│  Instance 1 │  │  Instance 2 │  │  Instance 3 │
└────────┬────┘  └───────┬─────┘  └──────┬──────┘
         │                │                │
         └────────────────┴────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
         ┌────▼────┐          ┌──────▼──────┐
         │PostgreSQL│          │    Redis    │
         │(Supabase)│          │   Cluster   │
         └─────────┘          └─────────────┘
```

### Scaling Strategy

**Application Layer:**
- Stateless design (no session storage)
- Redis for shared state
- Async/await for concurrency
- Connection pooling

**Database Layer:**
- Read replicas for scaling reads
- Connection pooling (SQLAlchemy)
- Query optimization with indexes
- Prepared statements

**Cache Layer:**
- Redis cluster for high availability
- Cache invalidation strategy
- TTL-based expiration
- Graceful degradation

### Performance Optimizations

**1. Database:**
- Indexes on foreign keys
- Composite indexes for common queries
- Query result caching
- Lazy loading relationships

**2. API:**
- Response compression (gzip)
- Pagination for large datasets
- Field selection (partial responses)
- Async database operations

**3. External APIs:**
- Request pooling
- Retry with exponential backoff
- Circuit breaker pattern
- Response caching

---

## Performance

### Target Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| API Response Time | < 200ms | P95, excluding external APIs |
| WhatsApp Response | < 3s | End-to-end (webhook → response) |
| Database Queries | < 50ms | P95, simple queries |
| Concurrent Users | 1,000+ | Per instance |
| Uptime | 99.9% | Monthly |

### Monitoring

**Application Metrics:**
- Request duration
- Error rates
- Throughput (req/s)
- Active connections

**Database Metrics:**
- Query duration
- Connection pool usage
- Slow query log
- Deadlocks

**External API Metrics:**
- Response times
- Error rates
- Rate limit usage
- Circuit breaker status

---

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────────────────┐
│                   CDN / DNS                             │
│                 (Cloudflare)                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Load Balancer / WAF                        │
│                                                         │
└────────┬───────────────────────┬────────────────────────┘
         │                       │
┌────────▼──────────┐   ┌───────▼──────────┐
│   Application     │   │   Application     │
│   Servers         │   │   Servers         │
│   (Docker)        │   │   (Docker)        │
└────────┬──────────┘   └───────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼─────┐
    │PostgreSQL│          │   Redis   │
    │(Supabase)│          │  (Managed)│
    └──────────┘          └───────────┘
```

### Infrastructure

**Hosting:**
- Cloud provider (AWS/GCP/Azure)
- Container orchestration (Docker/Kubernetes)
- Auto-scaling groups

**Database:**
- Supabase (managed PostgreSQL)
- Automatic backups
- Point-in-time recovery

**Cache:**
- Redis Cloud / ElastiCache
- Cluster mode enabled
- Automatic failover

**CI/CD:**
- GitHub Actions
- Automated testing
- Rolling deployments
- Blue-green deployment

---

## Future Enhancements

### Planned Features

1. **Real-Time Dashboard**
   - WebSocket connections
   - Live appointment updates
   - Real-time analytics

2. **Advanced Analytics**
   - Appointment trends
   - Customer insights
   - Revenue reporting
   - AI recommendations

3. **Additional Integrations**
   - Stripe payment processing
   - SMS notifications (Twilio)
   - Email campaigns (SendGrid)
   - CRM integration (Salesforce)

4. **Mobile App**
   - React Native
   - Push notifications
   - Offline support

5. **Advanced AI**
   - Sentiment analysis
   - Predictive scheduling
   - Automated follow-ups
   - Voice support

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-17
**Maintained By:** AutoAgenda Pro Team

# 🤖 AutoAgenda Pro

> AI-Powered WhatsApp Appointment Scheduling System

AutoAgenda Pro is a complete multi-tenant SaaS solution for automating appointment scheduling through WhatsApp using AI-powered conversational interfaces. Built with FastAPI, Claude AI, and modern async Python patterns.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Features](#-features)** | **[Quick Start](#-quick-start)** | **[Documentation](#-documentation)** | **[API Docs](docs/API.md)** | **[Architecture](docs/ARCHITECTURE.md)**

## 🎯 Features

### Core Capabilities

- ✨ **AI-Powered Conversations**: Natural language understanding with Claude AI (Anthropic) and GPT-4 support
- 💬 **WhatsApp Integration**: Two-way messaging via Evolution API with multi-instance support
- 📅 **Calendar Sync**: Automatic Google Calendar event creation, updates, and availability checking
- 🏢 **Multi-Tenant**: Complete data isolation for SaaS deployment
- 🔄 **Real-Time Processing**: Async/await patterns throughout for instant responses

### Technical Features

- 🗄️ **Robust Database**: PostgreSQL (Supabase) with SQLAlchemy 2.0 async ORM
- 🔐 **Secure Authentication**: JWT tokens with bcrypt password hashing
- ✅ **Data Validation**: Pydantic v2 schemas with Brazilian phone/CPF validation
- 📊 **Smart Caching**: Redis with graceful degradation
- 🐳 **Production Ready**: Docker, Alembic migrations, comprehensive logging
- 🌍 **Brazilian Optimized**: Timezone-aware, Portuguese language, local validators

### Business Features

- 📆 **Appointment Management**: Create, update, cancel with automatic notifications
- 👥 **Customer Management**: Complete CRM with conversation history
- ⚙️ **Configurable**: Business hours, services, message templates per tenant
- 🤖 **Intent Detection**: Automatic understanding of schedule/cancel/reschedule requests
- 📨 **Auto-Reminders**: Scheduled WhatsApp reminders before appointments
- 📈 **Scalable**: Designed for horizontal scaling

## 🛠️ Tech Stack

### Core Framework
- **FastAPI** 0.109.0 - Modern async web framework
- **Python** 3.11+ - Type-safe async programming
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic** v2 - Data validation and serialization

### Database & ORM
- **PostgreSQL** 14+ - Robust relational database (via Supabase)
- **SQLAlchemy** 2.0 - Async ORM with full type support
- **Asyncpg** - High-performance async PostgreSQL driver
- **Alembic** - Database migration management

### AI & Machine Learning
- **Anthropic Claude** 3.5 Sonnet - Primary LLM for conversations
- **OpenAI GPT-4** - Alternative/fallback LLM provider
- **LLM Factory Pattern** - Seamless provider switching

### External Integrations
- **Evolution API** - WhatsApp Business API integration
- **Google Calendar API** - Service Account authentication
- **Service Account** - Secure credential management

### Security & Authentication
- **JWT** - JSON Web Tokens (python-jose)
- **Bcrypt** - Password hashing (passlib)
- **HTTPBearer** - Token authentication scheme

### Caching & Performance
- **Redis** 7+ - In-memory data store
- **Connection Pooling** - SQLAlchemy pool management
- **Async I/O** - Non-blocking operations throughout

### DevOps & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Alembic** - Version-controlled migrations
- **Git** - Version control

## 📋 Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- PostgreSQL database (Supabase account)
- Anthropic API key
- Google Cloud project with Calendar API enabled
- Evolution API instance

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd autoagendaPro
```

### 2. Configure environment variables

```bash
cd backend
cp .env.example .env
```

Edit `.env` file and fill in your credentials:
- `DATABASE_URL`: Your Supabase PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Your Claude AI API key
- `GOOGLE_CALENDAR_CREDENTIALS`: Service account JSON credentials
- `EVOLUTION_API_URL` and `EVOLUTION_API_KEY`: Your Evolution API details
- `API_SECRET_KEY`: Generate a secure key (e.g., `openssl rand -hex 32`)

### 3. Run with Docker (Recommended)

```bash
# From project root
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### 4. Run locally (Development)

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

### 5. Access the API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
autoagenda-pro/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration and environment variables
│   │   ├── database.py          # Database connection and session management
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic (AI, Calendar, WhatsApp)
│   │   ├── routers/             # API endpoint routes
│   │   └── utils/               # Helper functions and utilities
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Docker image configuration
│   └── .env.example            # Environment variables template
├── database/                    # Database migrations and schemas
├── n8n/                        # N8N workflow configurations
├── docs/                       # Additional documentation
├── docker-compose.yml          # Docker Compose configuration
└── README.md                   # This file
```

## 🔧 Development

### Code Style

This project follows strict code quality standards:

- **Type Hints**: All functions must have type annotations
- **Async/Await**: Use async patterns throughout
- **Docstrings**: Google-style docstrings for all public functions
- **Formatting**: Black for code formatting
- **Linting**: Flake8 for code quality
- **Type Checking**: Mypy for static type analysis

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Code Quality Checks

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type check
mypy app/
```

## 🗄️ Database Setup

The application uses PostgreSQL via Supabase with async SQLAlchemy 2.0. Complete migration management with Alembic.

### Initial Setup

```bash
cd backend

# Generate initial migration from models
alembic revision --autogenerate -m "Initial schema"

# Apply all migrations
alembic upgrade head

# Seed test data (optional)
python -m database.seeds.initial_data
```

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Add column to users"

# Apply migrations
alembic upgrade head              # Apply all
alembic upgrade +1                # Apply next one

# Rollback migrations
alembic downgrade -1              # Rollback last
alembic downgrade base            # Rollback all

# Check status
alembic current                   # Show current version
alembic history                   # Show all versions
```

### Seed Data

The seed script creates:
- Test tenant: "Clínica Exemplo"
- Admin user: `admin@clinica-exemplo.com` / `admin123`
- 3 sample services
- Business configuration with default hours

```bash
# Seed initial data
python -m database.seeds.initial_data

# Clear all data (with confirmation)
python -m database.seeds.initial_data --clear
```

See [backend/database/README.md](backend/database/README.md) for complete database documentation.

## 🤖 N8N Workflows

N8N workflows automate various processes. See [n8n/README.md](n8n/README.md) for workflow configurations.

## 📚 API Documentation

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

### Main Endpoints

- `POST /api/v1/webhooks/whatsapp` - WhatsApp webhook receiver
- `GET /api/v1/appointments` - List appointments
- `POST /api/v1/appointments` - Create appointment
- `GET /health` - Health check endpoint

Full API documentation is available at `/docs` when running the application.

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy ORM
- CORS configuration
- Rate limiting
- Environment-based configuration

## 🌍 Environment Variables

See [backend/.env.example](backend/.env.example) for a complete list of required environment variables.

## 📖 Documentation

### Complete Guides

- **[API Reference](docs/API.md)** - Complete REST API documentation with examples
- **[Architecture](docs/ARCHITECTURE.md)** - System design, data flow, and scalability
- **[Database Setup](backend/database/README.md)** - Migrations, seeding, and schema

### Key Topics

- **Authentication**: JWT-based with refresh tokens
- **Multi-Tenant**: Complete tenant isolation strategies
- **WhatsApp Integration**: Evolution API setup and webhooks
- **AI Configuration**: LLM provider setup and customization
- **Google Calendar**: Service Account configuration
- **Deployment**: Production deployment strategies

### API Endpoints

See [docs/API.md](docs/API.md) for complete documentation. Quick reference:

```bash
# Authentication
POST   /api/v1/auth/register        # Register user
POST   /api/v1/auth/login          # Login
GET    /api/v1/auth/me             # Get current user

# Appointments
GET    /api/v1/appointments         # List appointments
POST   /api/v1/appointments         # Create appointment
PUT    /api/v1/appointments/{id}    # Update appointment
DELETE /api/v1/appointments/{id}    # Cancel appointment

# Customers
GET    /api/v1/customers            # List customers
POST   /api/v1/customers            # Create customer
GET    /api/v1/customers/phone/{phone}  # Find by phone

# Webhooks
POST   /api/v1/webhooks/whatsapp    # WhatsApp messages
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code:
- Passes all tests
- Follows the code style guidelines
- Includes appropriate documentation
- Has type hints for all functions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Anthropic](https://www.anthropic.com/) - Claude AI API
- [Supabase](https://supabase.com/) - Database hosting
- [Evolution API](https://evolution-api.com/) - WhatsApp integration
- [Google Calendar API](https://developers.google.com/calendar) - Calendar integration

## 📞 Support

For support, please open an issue in the GitHub repository.

---

**Built with ❤️ for automating appointment scheduling**

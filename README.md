# 🤖 AutoAgenda Pro

> Sistema inteligente de agendamento via WhatsApp com IA conversacional

AutoAgenda Pro é uma solução completa para automatização de agendamentos através do WhatsApp, utilizando inteligência artificial Claude para conversas naturais, integração com Google Calendar e Evolution API para mensagens.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Features

- ✨ **Conversação Natural com IA**: Utiliza Claude AI (Anthropic) para entender e responder em linguagem natural
- 📅 **Integração com Google Calendar**: Sincronização automática de compromissos
- 💬 **WhatsApp Business**: Comunicação via Evolution API
- 🗄️ **Banco de Dados Robusto**: PostgreSQL via Supabase com suporte assíncrono
- 🚀 **Alta Performance**: Async/await patterns em toda a aplicação
- 🔒 **Seguro**: Autenticação JWT, validação de dados com Pydantic v2
- 🐳 **Docker Ready**: Containerização completa para fácil deployment
- 📊 **Cache Inteligente**: Redis para otimização de performance
- 🔄 **Workflows Automatizados**: Integração com N8N

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Language**: Python 3.11+
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Cache**: Redis

### AI & Integrations
- **AI**: Anthropic Claude API
- **Calendar**: Google Calendar API
- **WhatsApp**: Evolution API
- **Automation**: N8N Workflows

### DevOps
- **Containerization**: Docker & Docker Compose
- **ASGI Server**: Uvicorn
- **Process Manager**: Gunicorn (production)

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

The application uses PostgreSQL via Supabase. See [database/README.md](database/README.md) for detailed setup instructions.

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

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

## 📖 Additional Documentation

- [Database Setup](database/README.md)
- [N8N Workflows](n8n/README.md)
- [API Documentation](docs/README.md)

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

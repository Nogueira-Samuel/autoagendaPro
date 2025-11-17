# 📚 AutoAgenda Pro Documentation

Welcome to the AutoAgenda Pro documentation hub. This directory contains detailed documentation for all aspects of the system.

## 📑 Table of Contents

### Getting Started
- [Quick Start Guide](getting-started.md) *(Coming Soon)*
- [Installation](installation.md) *(Coming Soon)*
- [Configuration](configuration.md) *(Coming Soon)*

### Architecture
- [System Architecture](architecture/system-overview.md) *(Coming Soon)*
- [Database Schema](architecture/database-schema.md) *(Coming Soon)*
- [API Design](architecture/api-design.md) *(Coming Soon)*
- [Security Model](architecture/security.md) *(Coming Soon)*

### API Documentation
- [API Overview](api/overview.md) *(Coming Soon)*
- [Authentication](api/authentication.md) *(Coming Soon)*
- [Webhooks](api/webhooks.md) *(Coming Soon)*
- [Appointments](api/appointments.md) *(Coming Soon)*
- [Users](api/users.md) *(Coming Soon)*

### Integrations
- [Claude AI Integration](integrations/claude-ai.md) *(Coming Soon)*
- [Google Calendar Setup](integrations/google-calendar.md) *(Coming Soon)*
- [Evolution API Configuration](integrations/evolution-api.md) *(Coming Soon)*
- [N8N Workflows](integrations/n8n-workflows.md) *(Coming Soon)*

### Development
- [Development Setup](development/setup.md) *(Coming Soon)*
- [Code Style Guide](development/code-style.md) *(Coming Soon)*
- [Testing Guide](development/testing.md) *(Coming Soon)*
- [Contributing](development/contributing.md) *(Coming Soon)*

### Deployment
- [Docker Deployment](deployment/docker.md) *(Coming Soon)*
- [Production Checklist](deployment/production-checklist.md) *(Coming Soon)*
- [Environment Variables](deployment/environment-variables.md) *(Coming Soon)*
- [Monitoring & Logging](deployment/monitoring.md) *(Coming Soon)*

### User Guides
- [Admin Dashboard](user-guides/admin-dashboard.md) *(Coming Soon)*
- [WhatsApp Bot Usage](user-guides/whatsapp-bot.md) *(Coming Soon)*
- [Managing Appointments](user-guides/appointments.md) *(Coming Soon)*

## 🚀 Quick Links

### For Developers

- **[Main README](../README.md)** - Project overview and quick start
- **[Database README](../database/README.md)** - Database setup and schema
- **[N8N README](../n8n/README.md)** - Workflow automation setup

### For API Users

- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger UI (when running locally)
- **[Alternative API Docs](http://localhost:8000/redoc)** - ReDoc UI (when running locally)

### For System Administrators

- **[Docker Compose](../docker-compose.yml)** - Container orchestration
- **[Environment Template](../backend/.env.example)** - Configuration reference

## 📖 Documentation Structure

```
docs/
├── README.md                    # This file
├── getting-started.md           # Quick start guide
├── installation.md              # Detailed installation instructions
├── configuration.md             # Configuration guide
│
├── architecture/                # System architecture docs
│   ├── system-overview.md
│   ├── database-schema.md
│   ├── api-design.md
│   └── security.md
│
├── api/                        # API documentation
│   ├── overview.md
│   ├── authentication.md
│   ├── webhooks.md
│   ├── appointments.md
│   └── users.md
│
├── integrations/               # Integration guides
│   ├── claude-ai.md
│   ├── google-calendar.md
│   ├── evolution-api.md
│   └── n8n-workflows.md
│
├── development/                # Development guides
│   ├── setup.md
│   ├── code-style.md
│   ├── testing.md
│   └── contributing.md
│
├── deployment/                 # Deployment guides
│   ├── docker.md
│   ├── production-checklist.md
│   ├── environment-variables.md
│   └── monitoring.md
│
└── user-guides/                # End-user guides
    ├── admin-dashboard.md
    ├── whatsapp-bot.md
    └── appointments.md
```

## 🎯 Key Concepts

### Conversation Flow

1. **User sends WhatsApp message** → Evolution API
2. **Webhook triggers** → FastAPI backend
3. **Message processed by** → Claude AI
4. **AI determines intent** → Appointment creation, query, or general conversation
5. **Action executed** → Database update, Calendar integration
6. **Response sent** → Via Evolution API to WhatsApp

### System Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Backend API** | Core business logic | FastAPI + Python |
| **Database** | Data persistence | PostgreSQL (Supabase) |
| **AI Engine** | Natural conversation | Claude AI (Anthropic) |
| **Calendar** | Appointment scheduling | Google Calendar API |
| **Messaging** | WhatsApp interface | Evolution API |
| **Automation** | Workflow orchestration | N8N |
| **Cache** | Performance optimization | Redis |

## 🔧 Environment Setup

### Required Accounts

1. **Supabase** - PostgreSQL database
   - Sign up: https://supabase.com
   - Create project
   - Get database URL

2. **Anthropic** - Claude AI API
   - Sign up: https://console.anthropic.com
   - Get API key
   - Choose model: claude-3-5-sonnet-20241022

3. **Google Cloud** - Calendar API
   - Create project: https://console.cloud.google.com
   - Enable Calendar API
   - Create service account
   - Download credentials JSON

4. **Evolution API** - WhatsApp integration
   - Deploy instance: https://evolution-api.com
   - Get API URL and key

### Development Tools

- **Python 3.11+** - Programming language
- **Docker** - Containerization
- **Git** - Version control
- **VS Code** (recommended) - Code editor
- **Postman** or **Insomnia** - API testing

## 📝 Contributing to Documentation

Documentation contributions are welcome! To add or update documentation:

1. Fork the repository
2. Create a new branch: `git checkout -b docs/your-topic`
3. Add your documentation in the appropriate section
4. Use Markdown format
5. Include code examples where relevant
6. Add images to `docs/images/` if needed
7. Update this README to link to your new docs
8. Submit a pull request

### Documentation Style Guide

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep paragraphs short
- Use headers to organize content
- Include links to related documentation
- Add a table of contents for long documents

## 🔍 Search Documentation

Use your editor's search functionality to find specific topics across all documentation files.

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@autoagendapro.com *(Coming Soon)*

## 📅 Documentation Updates

This documentation is continuously updated. Last major update: 2024-01

## 🌟 Next Steps

1. **New Users**: Start with the [Quick Start Guide](getting-started.md)
2. **Developers**: Check [Development Setup](development/setup.md)
3. **API Integration**: Read [API Overview](api/overview.md)
4. **Deployment**: Follow [Docker Deployment](deployment/docker.md)

---

**Note**: Documentation marked as *(Coming Soon)* will be added in future updates. Feel free to contribute!

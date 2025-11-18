# 🤖 AutoAgenda Pro

> Sistema inteligente de agendamento via WhatsApp com IA conversacional

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AutoAgenda Pro é uma solução completa multi-tenant para automatização de agendamentos através do WhatsApp, utilizando inteligência artificial conversacional. Construído com FastAPI, Claude AI/GPT-4 e padrões modernos de Python assíncrono.

---

## ✨ Funcionalidades

### Principais Recursos

- 🤖 **Conversação com IA**: Processamento de linguagem natural com Claude AI e GPT-4
- 💬 **Integração WhatsApp**: Mensagens bidirecionais via Evolution API
- 📅 **Sincronização de Agenda**: Criação automática de eventos no Google Calendar
- 🏢 **Multi-Tenant**: Arquitetura SaaS completa com isolamento de dados
- 🔄 **Processamento em Tempo Real**: Padrões async/await para respostas instantâneas

### Recursos Técnicos

- 🔐 **Segurança**: Autenticação JWT, senhas bcrypt, controle de acesso baseado em funções (RBAC)
- 🗄️ **Banco de Dados**: PostgreSQL com SQLAlchemy 2.0 assíncrono
- ⚡ **Cache Inteligente**: Redis para otimização de performance
- 🐳 **Docker**: Containerização completa para deploy facilitado
- 📊 **Validação**: Pydantic v2 para validação robusta de dados
- 🔄 **Migrations**: Alembic para versionamento de banco de dados

---

## 🛠️ Stack Tecnológica

**Backend:** FastAPI 0.109.0, Python 3.11+, SQLAlchemy 2.0
**Banco de Dados:** PostgreSQL (Supabase), Redis
**Inteligência Artificial:** OpenAI GPT-3.5/4, Anthropic Claude
**Integrações:** Google Calendar API v3, Evolution API v2
**DevOps:** Docker, Docker Compose, Coolify

---

## 🚀 Começando

### Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL (recomendamos Supabase)
- Docker + Docker Compose (opcional)
- Chave de API OpenAI ou Anthropic
- Service Account do Google Calendar
- Instância do Evolution API

### Instalação Local
```bash
# Clonar repositório
git clone <seu-repositorio>
cd autoagendaPro/backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas credenciais

# Executar migrations
alembic upgrade head

# Popular dados iniciais (opcional)
python -m database.seeds.initial_data

# Iniciar servidor de desenvolvimento
uvicorn app.main:app --reload
```

**Servidor:** http://localhost:8000
**Documentação interativa:** http://localhost:8000/docs

### Instalação com Docker
```bash
# A partir da raiz do projeto
docker-compose up -d

# Executar migrations
docker-compose exec backend alembic upgrade head
```

---

## 📖 Documentação

### Guias Completos

- **[Referência da API](docs/API.md)** - Documentação completa da API REST com exemplos
- **[Arquitetura do Sistema](docs/ARCHITECTURE.md)** - Design do sistema, fluxo de dados e escalabilidade
- **[Configuração do Banco](backend/database/README.md)** - Migrations, seeds e schema

### Tópicos Principais

- **Autenticação**: Sistema JWT com refresh tokens
- **Multi-Tenant**: Estratégias de isolamento completo de dados
- **Integração WhatsApp**: Configuração Evolution API e webhooks
- **Configuração de IA**: Setup de provedores LLM e customização
- **Google Calendar**: Configuração de Service Account

---

## 🔧 Configuração

Principais variáveis de ambiente (veja `.env.example` para lista completa):
```bash
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@host:5432/banco

# Provedores de IA
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# WhatsApp (Evolution API)
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-chave

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS={"type":"service_account",...}

# Segurança
API_SECRET_KEY=sua-chave-secreta-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Ambiente
ENVIRONMENT=production
DEBUG=false
```

---

## 📊 Estrutura do Projeto
autoagendaPro/
├── backend/
│   ├── app/
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Lógica de negócio (LLM, Calendar, WhatsApp)
│   │   ├── routers/        # Endpoints da API
│   │   ├── utils/          # Utilitários (auth, validators, security)
│   │   └── middleware/     # Middleware (tenant, auth)
│   ├── alembic/            # Migrations do banco de dados
│   ├── database/           # Seeds e documentação
│   │   └── seeds/          # Scripts de dados iniciais
│   ├── requirements.txt    # Dependências Python
│   └── .env.example        # Exemplo de variáveis de ambiente
├── docs/                   # Documentação do projeto
├── docker-compose.yml      # Configuração Docker
└── README.md              # Este arquivo

---

## 📝 Principais Endpoints
POST   /api/v1/auth/register          # Cadastro de usuário
POST   /api/v1/auth/login             # Login (retorna JWT)
GET    /api/v1/appointments           # Listar agendamentos
POST   /api/v1/appointments           # Criar agendamento
DELETE /api/v1/appointments/{id}      # Cancelar agendamento
GET    /api/v1/customers              # Listar clientes
POST   /api/v1/customers              # Criar cliente
POST   /api/v1/webhooks/whatsapp      # Webhook do WhatsApp

Documentação completa da API: [docs/API.md](docs/API.md)

---

## 🗄️ Configuração do Banco de Dados

O sistema utiliza PostgreSQL via Supabase com SQLAlchemy 2.0 assíncrono e gerenciamento completo de migrations via Alembic.

### Configuração Inicial
```bash
# Criar migration inicial (se necessário)
cd backend
alembic revision --autogenerate -m "Initial schema"

# Aplicar migrations
alembic upgrade head

# Verificar versão atual
alembic current

# Rollback (se necessário)
alembic downgrade -1
```

### Dados Iniciais
```bash
# Popular banco com dados de exemplo
python -m database.seeds.initial_data

# Credenciais padrão:
# Email: admin@clinica-exemplo.com
# Senha: admin123
```

---

## 🧪 Testes
```bash
# Executar testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Abrir relatório de cobertura
open htmlcov/index.html
```

---

## 🚢 Deploy

### Deploy com Coolify (Recomendado)

1. Conectar repositório GitHub no Coolify
2. Configurar variáveis de ambiente na interface
3. Fazer deploy automático a partir da branch
4. Executar migrations: `alembic upgrade head`

### Deploy Manual com Docker
```bash
# Build e iniciar containers
docker-compose up -d --build

# Executar migrations
docker-compose exec backend alembic upgrade head

# Ver logs
docker-compose logs -f backend

# Parar containers
docker-compose down
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

---

## 💬 Suporte

- **Documentação Completa**: Diretório `docs/`
- **Issues**: GitHub Issues
- **Email**: [seu-email@exemplo.com]

---

**Desenvolvido com ❤️ para automatizar agendamentos e melhorar o atendimento ao cliente**

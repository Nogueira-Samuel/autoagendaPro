# 🚀 AutoAgenda Pro - Backend API

Sistema inteligente de agendamento automatizado via WhatsApp com IA conversacional.

![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

### 🤖 IA Conversacional
- **OpenAI GPT** para entender linguagem natural
- Agendamento automático via WhatsApp
- Contexto de conversa mantido
- Prompt customizável por tenant

### 📅 Sistema de Agendamentos
- CRUD completo de agendamentos
- Status: pendente, confirmado, completado, cancelado, no-show
- Filtros avançados (data, status, cliente, serviço)
- Multi-tenant (isolamento por empresa)

### 🔔 Notificações Automáticas ⭐ NEW!
- **Sistema 100% independente** (sem Google Calendar)
- Confirmação imediata ao agendar
- Lembrete 24 horas antes
- Lembrete 1 hora antes
- Agradecimento pós-consulta
- Notificações para donos do negócio
- Logs completos de envios

### 📱 Integração WhatsApp
- Evolution API para envio/recebimento
- Webhooks para mensagens em tempo real
- Suporte multi-instâncias
- QR Code para conectar

### 🏢 Multi-tenant
- Isolamento completo de dados
- Configurações por empresa
- Usuários e permissões
- Planos (básico, premium)

---

## 🛠️ Stack Tecnológica
```json
{
  "framework": "FastAPI 0.104",
  "language": "Python 3.11",
  "database": "PostgreSQL 15",
  "orm": "SQLAlchemy 2.0",
  "migrations": "Alembic 1.12",
  "auth": "JWT (python-jose)",
  "scheduler": "APScheduler 3.10",
  "ai": "OpenAI GPT-4",
  "whatsapp": "Evolution API"
}
```

---

## 🚀 Getting Started

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- Evolution API (WhatsApp)
- OpenAI API Key

### Instalação
```bash
# Clone o repositório
git clone https://github.com/Nogueira-Samuel/autoagendaPro.git
cd autoagendaPro/backend

# Crie ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Execute migrações
alembic upgrade head

# Crie tenant e usuário admin
python create_admin.py

# Inicie o servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: `http://localhost:8000/docs` (Swagger UI)

---

## ⚙️ Configuração (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/autoagenda

# Security
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Evolution API (WhatsApp)
EVOLUTION_API_URL=https://your-evolution-api.com
EVOLUTION_API_KEY=your-api-key

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Notification Settings
NOTIFICATION_REMINDER_24H=true
NOTIFICATION_REMINDER_1H=true
NOTIFICATION_CONFIRMATION=true
NOTIFICATION_THANKS=true
```

---

## 📊 Estrutura do Banco
```
tenants (empresas)
├── users (usuários do dashboard)
├── customers (clientes finais)
├── services (serviços oferecidos)
├── appointments (agendamentos)
├── business_config (configurações)
├── conversations (histórico IA)
└── notification_logs (⭐ NEW - logs de notificações)
```

---

## 🔔 Sistema de Notificações

### Jobs Automáticos

**1. Lembrete 24h antes**
- Roda: A cada 30 minutos
- Envia: Para agendamentos confirmados de amanhã

**2. Lembrete 1h antes**
- Roda: A cada 10 minutos
- Envia: Para agendamentos na próxima hora

**3. Agradecimento**
- Roda: Diariamente às 9:00 AM
- Envia: Para consultas completadas ontem

### API Endpoints
```
GET  /api/v1/notifications
     Lista todas as notificações (com filtros)

GET  /api/v1/notifications/stats
     Estatísticas de envios

POST /api/v1/notifications/test/confirmation/{id}
     Testa confirmação de agendamento

POST /api/v1/notifications/test/reminder/{id}
     Testa lembretes (24h ou 1h)
```

### Templates de Mensagens

Customizáveis em `business_config`:
- `confirmation_message_template`
- `reminder_message_template`
- `cancellation_message_template`

Variáveis disponíveis:
- `{name}` - Nome do cliente
- `{date}` - Data formatada
- `{time}` - Horário
- `{service}` - Nome do serviço
- `{price}` - Preço
- `{business_name}` - Nome da empresa

---

## 🌐 API Endpoints

### Autenticação
```
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

### Agendamentos
```
GET    /api/v1/appointments
GET    /api/v1/appointments/{id}
POST   /api/v1/appointments
PUT    /api/v1/appointments/{id}
DELETE /api/v1/appointments/{id}
```

### Clientes
```
GET    /api/v1/customers
POST   /api/v1/customers
PUT    /api/v1/customers/{id}
```

### Serviços
```
GET    /api/v1/services
POST   /api/v1/services
PUT    /api/v1/services/{id}
DELETE /api/v1/services/{id}
```

### Configurações
```
GET /api/v1/business-config/{tenant_id}
PUT /api/v1/business-config/{tenant_id}
```

### WhatsApp
```
POST /api/v1/whatsapp/webhook
GET  /api/v1/whatsapp/qr/{instance}
POST /api/v1/whatsapp/test
```

### Notificações ⭐ NEW
```
GET  /api/v1/notifications
GET  /api/v1/notifications/stats
POST /api/v1/notifications/test/confirmation/{id}
POST /api/v1/notifications/test/reminder/{id}
```

---

## 🚀 Deploy (VPS)

### Preparação
```bash
# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib

# Clonar projeto
cd /var/www
git clone https://github.com/Nogueira-Samuel/autoagendaPro.git
cd autoagendaPro/backend
```

### Configuração
```bash
# Ambiente virtual
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env (ajuste valores)
nano .env

# Migrações
alembic upgrade head
python create_admin.py
```

### Serviço Systemd
```bash
sudo nano /etc/systemd/system/autoagenda-backend.service
```
```ini
[Unit]
Description=AutoAgenda Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/autoagendaPro/backend
Environment="PATH=/var/www/autoagendaPro/backend/venv/bin"
ExecStart=/var/www/autoagendaPro/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
# Iniciar serviço
sudo systemctl daemon-reload
sudo systemctl start autoagenda-backend
sudo systemctl enable autoagenda-backend

# Verificar status
sudo systemctl status autoagenda-backend

# Ver logs
sudo journalctl -u autoagenda-backend -f
```

---

## 📝 Logs do Scheduler

O scheduler gera logs automáticos:
```
INFO:     Starting notification scheduler...
INFO:     Scheduler started successfully!
INFO:     Running 24h reminder job...
INFO:     Found 5 appointments for tomorrow
INFO:     24h reminder sent for appointment 123: True
```

---

## 🧪 Testes
```bash
# Testar endpoints manualmente
http://localhost:8000/docs

# Testar notificação de confirmação
curl -X POST "http://localhost:8000/api/v1/notifications/test/confirmation/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Ver estatísticas
curl "http://localhost:8000/api/v1/notifications/stats?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔄 Atualizar Código
```bash
cd /var/www/autoagendaPro/backend
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart autoagenda-backend
```

---

## 🐛 Troubleshooting

### Scheduler não inicia
```bash
# Ver logs
journalctl -u autoagenda-backend -f

# Verificar se APScheduler está instalado
pip list | grep APScheduler

# Reinstalar
pip install APScheduler==3.10.4
```

### Notificações não enviando
```bash
# Verificar variáveis de ambiente
cat .env | grep EVOLUTION

# Testar Evolution API manualmente
curl -X POST "https://your-evolution-api.com/message/sendText/tenant_1" \
  -H "apikey: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"number": "5521999999999", "text": "Teste"}'
```

### Banco de dados
```bash
# Conectar ao PostgreSQL
psql -U autoagenda_user -d autoagenda

# Ver tabelas
\dt

# Ver notification_logs
SELECT * FROM notification_logs ORDER BY created_at DESC LIMIT 10;
```

---

## 📚 Documentação Adicional

- [Swagger UI](http://localhost:8000/docs) - Documentação interativa da API
- [ReDoc](http://localhost:8000/redoc) - Documentação alternativa

---

## 🔒 Segurança

- JWT para autenticação
- Senhas hasheadas com bcrypt
- CORS configurável
- Variáveis sensíveis em .env
- Isolamento multi-tenant

---

## 📝 License

MIT © AutoAgenda Pro

---

## 👨‍💻 Autor

**Samuel Nogueira**
- GitHub: [@Nogueira-Samuel](https://github.com/Nogueira-Samuel)

---

## 🙏 Agradecimentos

- FastAPI
- SQLAlchemy
- APScheduler
- Evolution API
- OpenAI

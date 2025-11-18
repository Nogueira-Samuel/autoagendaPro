# Guia de Troubleshooting - AutoAgenda Pro

Guia completo para solução de problemas do AutoAgenda Pro.

## Índice

- [Como Usar Este Guia](#como-usar-este-guia)
- [Problemas com Banco de Dados](#problemas-com-banco-de-dados)
- [Problemas com WhatsApp](#problemas-com-whatsapp)
- [Problemas com Google Calendar](#problemas-com-google-calendar)
- [Problemas com IA (LLM)](#problemas-com-ia-llm)
- [Problemas de Autenticação](#problemas-de-autenticação)
- [Problemas de Performance](#problemas-de-performance)
- [Problemas com Docker](#problemas-com-docker)
- [Problemas Gerais](#problemas-gerais)
- [Como Debugar](#como-debugar)
- [Quando Pedir Ajuda](#quando-pedir-ajuda)

---

## Como Usar Este Guia

1. **Identifique o problema**: Leia a descrição dos sintomas
2. **Verifique a causa**: Siga os passos de diagnóstico
3. **Aplique a solução**: Execute os comandos sugeridos
4. **Teste**: Confirme que o problema foi resolvido
5. **Documente**: Anote o que foi feito para referência futura

**Legenda**:
- 🔴 **Crítico** - Sistema não funciona
- 🟡 **Importante** - Funcionalidade afetada
- 🟢 **Menor** - Problema estético ou não crítico

---

## Problemas com Banco de Dados

### 🔴 Erro: "Connection refused" ao conectar no banco

**Sintomas**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
could not connect to server: Connection refused
```

**Causas Possíveis**:
1. DATABASE_URL incorreta
2. Supabase fora do ar
3. Firewall bloqueando conexão
4. Limite de conexões atingido

**Diagnóstico**:

```bash
# 1. Testar conexão direta com PostgreSQL
psql "$DATABASE_URL"

# 2. Verificar se DATABASE_URL está correta
echo $DATABASE_URL

# 3. Testar com curl (se for Supabase)
curl -I https://db.xxx.supabase.co
```

**Solução**:

```bash
# Opção 1: Verificar e corrigir DATABASE_URL no .env
nano .env
# DATABASE_URL=postgresql://user:pass@host:port/db

# Opção 2: Usar connection pooler do Supabase
# Trocar porta 5432 por 6543 e adicionar ?pgbouncer=true
DATABASE_URL="postgresql://postgres:senha@host:6543/postgres?pgbouncer=true"

# Opção 3: Reiniciar aplicação
docker compose restart backend

# Opção 4: Verificar status do Supabase
# Acessar: https://status.supabase.com
```

---

### 🔴 Erro: "Too many connections"

**Sintomas**:
```
FATAL: sorry, too many clients already
```

**Causa**: Limite de conexões PostgreSQL atingido

**Solução Imediata**:

```bash
# 1. Matar conexões idle
docker compose exec backend psql $DATABASE_URL -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle'
  AND pid <> pg_backend_pid();
"

# 2. Ver conexões ativas
docker compose exec backend psql $DATABASE_URL -c "
  SELECT count(*) as total_connections,
         state,
         application_name
  FROM pg_stat_activity
  GROUP BY state, application_name;
"
```

**Solução Permanente**:

```python
# Ajustar pool de conexões em app/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,          # Reduzir de 10 para 5
    max_overflow=5,       # Reduzir de 20 para 5
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

### 🟡 Erro: "Migration already exists" ou "Duplicate revision"

**Sintomas**:
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Diagnóstico**:

```bash
# Ver status das migrations
alembic current

# Ver histórico
alembic history

# Ver pending migrations
alembic upgrade --sql head > pending.sql
cat pending.sql
```

**Solução**:

```bash
# Opção 1: Forçar upgrade para latest
alembic upgrade head

# Opção 2: Downgrade e upgrade novamente
alembic downgrade -1
alembic upgrade head

# Opção 3: Marcar como executada sem rodar SQL (USE COM CUIDADO!)
alembic stamp head

# Opção 4: Reconstruir do zero (PERDA DE DADOS!)
# Apenas em desenvolvimento!
alembic downgrade base
alembic upgrade head
```

---

### 🟡 Dados não aparecem ou estão incorretos

**Sintomas**: Query retorna vazio mas deveria ter dados

**Diagnóstico**:

```sql
-- 1. Verificar se tenant existe
SELECT * FROM tenants WHERE id = 1;

-- 2. Verificar isolation de tenant (tenant_id correto?)
SELECT * FROM appointments WHERE tenant_id = 1;

-- 3. Verificar dados deletados (soft delete)
SELECT * FROM appointments WHERE tenant_id = 1 AND deleted_at IS NULL;

-- 4. Ver total de registros
SELECT
    'tenants' as table_name, COUNT(*) as total FROM tenants
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'appointments', COUNT(*) FROM appointments;
```

**Solução**:

```sql
-- Restaurar registro deletado acidentalmente
UPDATE appointments
SET deleted_at = NULL, updated_at = NOW()
WHERE id = 123;

-- Corrigir tenant_id incorreto
UPDATE customers
SET tenant_id = 1
WHERE id = 456 AND tenant_id != 1;
```

---

## Problemas com WhatsApp

### 🔴 WhatsApp desconectado / QR Code não funciona

**Sintomas**:
- QR Code não aparece
- Após escanear, não conecta
- Status = "close" ou "connecting"

**Diagnóstico**:

```bash
# 1. Verificar status da instância
curl -X GET "https://evolution.seudominio.com/instance/connectionState/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE"

# Resposta esperada: {"state": "open"}

# 2. Listar todas as instâncias
curl -X GET "https://evolution.seudominio.com/instance/fetchInstances" \
  -H "apikey: SUA-CHAVE"

# 3. Ver logs do Evolution API
docker logs evolution-api -f --tail 100
```

**Solução**:

```bash
# Opção 1: Gerar novo QR Code
curl -X GET "https://evolution.seudominio.com/instance/connect/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE"

# Opção 2: Reiniciar instância
curl -X PUT "https://evolution.seudominio.com/instance/restart/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE"

# Opção 3: Deletar e recriar instância
curl -X DELETE "https://evolution.seudominio.com/instance/delete/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE"

# Recriar
curl -X POST "https://evolution.seudominio.com/instance/create" \
  -H "apikey: SUA-CHAVE" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "NOME-INSTANCIA",
    "qrcode": true,
    "webhook": {
      "url": "https://api.seudominio.com/api/v1/webhooks/whatsapp",
      "events": ["messages.upsert"]
    }
  }'

# Opção 4: Verificar se WhatsApp Web está logado em outro lugar
# Cliente deve desconectar outros aparelhos no WhatsApp
```

---

### 🟡 Mensagens não chegam no webhook

**Sintomas**: Cliente envia mensagem mas API não recebe

**Diagnóstico**:

```bash
# 1. Verificar webhook configurado
curl -X GET "https://evolution.seudominio.com/webhook/find/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE"

# 2. Ver logs da API (filtrar por webhook)
docker compose logs backend | grep -i webhook

# 3. Testar se webhook URL está acessível
curl -X POST "https://api.seudominio.com/api/v1/webhooks/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "instance": "test",
    "data": {
      "key": {"remoteJid": "5511999999999@s.whatsapp.net"},
      "message": {"conversation": "teste"}
    }
  }'
```

**Solução**:

```bash
# Opção 1: Reconfigurar webhook
curl -X PUT "https://evolution.seudominio.com/webhook/set/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.seudominio.com/api/v1/webhooks/whatsapp",
    "enabled": true,
    "events": [
      "messages.upsert",
      "connection.update"
    ]
  }'

# Opção 2: Verificar se API está rodando
curl https://api.seudominio.com/health

# Opção 3: Verificar firewall/CORS
# Webhook precisa ser acessível externamente

# Opção 4: Usar ngrok para testar localmente
ngrok http 8000
# Usar URL do ngrok como webhook temporário
```

---

### 🟡 API não responde mensagens do WhatsApp

**Sintomas**: Webhook recebe mensagem mas não envia resposta

**Diagnóstico**:

```bash
# 1. Ver logs do processamento
docker compose logs backend | grep -A 20 "messages.upsert"

# 2. Verificar se LLM está funcionando
curl -X POST "https://api.seudominio.com/api/v1/llm/test" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, teste"}'

# 3. Verificar se tenant está ativo
docker compose exec backend psql $DATABASE_URL -c "
  SELECT id, name, is_active, whatsapp_instance
  FROM tenants
  WHERE whatsapp_instance = 'NOME-INSTANCIA';
"
```

**Solução**:

```bash
# Opção 1: Verificar API Keys da IA
nano .env
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

docker compose restart backend

# Opção 2: Ativar tenant
docker compose exec backend psql $DATABASE_URL -c "
  UPDATE tenants
  SET is_active = true
  WHERE whatsapp_instance = 'NOME-INSTANCIA';
"

# Opção 3: Verificar configuração do webhook no código
# Arquivo: app/routers/webhooks.py
# Verificar se processamento está correto

# Opção 4: Testar envio manual
curl -X POST "https://evolution.seudominio.com/message/sendText/NOME-INSTANCIA" \
  -H "apikey: SUA-CHAVE" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5511999999999",
    "text": "Teste de resposta manual"
  }'
```

---

## Problemas com Google Calendar

### 🔴 Eventos não são criados no Google Calendar

**Sintomas**: Agendamento salvo no banco mas não aparece no Calendar

**Diagnóstico**:

```bash
# 1. Verificar Calendar ID configurado
docker compose exec backend psql $DATABASE_URL -c "
  SELECT tenant_id, google_calendar_id
  FROM business_config
  WHERE tenant_id = 1;
"

# 2. Ver logs de criação de evento
docker compose logs backend | grep -i "calendar"

# 3. Testar credenciais do Google
python -c "
import json
import os
from google.oauth2 import service_account

creds_json = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
creds_dict = json.loads(creds_json)
credentials = service_account.Credentials.from_service_account_info(creds_dict)
print('Credenciais válidas!')
"
```

**Solução**:

```bash
# Opção 1: Verificar credenciais no .env
nano .env
# GOOGLE_CALENDAR_CREDENTIALS deve ser JSON completo válido

# Opção 2: Testar permissões do Service Account
# Cliente deve compartilhar calendário com:
# autoagenda@seu-projeto.iam.gserviceaccount.com
# Permissão: "Fazer alterações em eventos"

# Opção 3: Verificar Calendar ID
# Formato correto:
# abc123@group.calendar.google.com (calendário secundário)
# usuario@gmail.com (calendário principal)

# Opção 4: Recriar Service Account
# 1. Google Cloud Console → IAM → Service Accounts
# 2. Criar nova Service Account
# 3. Baixar JSON key
# 4. Atualizar .env
# 5. Cliente compartilhar calendário novamente
```

---

### 🟡 Erro: "Insufficient Permission" ao criar evento

**Sintomas**:
```
googleapiclient.errors.HttpError: 403 Insufficient Permission
```

**Causa**: Service Account sem permissão no calendário

**Solução**:

```
INSTRUÇÕES PARA O CLIENTE:

1. Abra Google Calendar: https://calendar.google.com

2. Localize o calendário usado para agendamentos

3. Clique nos 3 pontos ao lado → "Configurações e compartilhamento"

4. Role até "Compartilhar com pessoas específicas"

5. Adicione o e-mail da Service Account:
   autoagenda@seu-projeto.iam.gserviceaccount.com

6. IMPORTANTE: Selecione permissão "Fazer alterações em eventos"
   (NÃO use "Ver somente detalhes")

7. Desmarque "Enviar convite por e-mail"

8. Clique "Enviar"

9. Aguarde 1-2 minutos para propagação

10. Teste novamente
```

---

### 🟡 Eventos duplicados no Google Calendar

**Sintomas**: Mesmo agendamento aparece várias vezes no calendário

**Causa**: Múltiplas tentativas de criar evento ou webhook duplicado

**Solução**:

```sql
-- 1. Verificar eventos duplicados no banco
SELECT
    appointment_date,
    customer_id,
    service_id,
    google_event_id,
    COUNT(*) as duplicates
FROM appointments
WHERE tenant_id = 1
  AND deleted_at IS NULL
GROUP BY appointment_date, customer_id, service_id, google_event_id
HAVING COUNT(*) > 1;

-- 2. Deletar duplicatas (manter apenas o mais recente)
DELETE FROM appointments a
WHERE id NOT IN (
    SELECT MAX(id)
    FROM appointments
    WHERE tenant_id = 1
      AND deleted_at IS NULL
    GROUP BY appointment_date, customer_id, service_id
)
AND tenant_id = 1;

-- 3. Verificar se webhook não está cadastrado múltiplas vezes
-- Ver configuração do Evolution API
```

---

## Problemas com IA (LLM)

### 🔴 Erro: "Invalid API Key" (Anthropic/OpenAI)

**Sintomas**:
```
AuthenticationError: Invalid API Key
```

**Diagnóstico**:

```bash
# 1. Verificar se API Key está no .env
cat .env | grep -i api_key

# 2. Testar Anthropic API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hi"}]
  }'

# 3. Testar OpenAI API
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 50
  }'
```

**Solução**:

```bash
# Opção 1: Gerar nova API Key
# Anthropic: https://console.anthropic.com/settings/keys
# OpenAI: https://platform.openai.com/api-keys

# Opção 2: Atualizar .env
nano .env
# ANTHROPIC_API_KEY=sk-ant-api03-xxx
# OPENAI_API_KEY=sk-xxx

# Reiniciar aplicação
docker compose restart backend

# Opção 3: Verificar créditos
# Anthropic Console → Billing
# OpenAI Dashboard → Usage
```

---

### 🟡 Timeout ao chamar LLM

**Sintomas**: Demora muito e retorna timeout

**Causa**: Prompt muito longo ou API lenta

**Solução**:

```python
# Ajustar timeout em app/services/llm_service.py

# Para Anthropic
client = anthropic.Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=60.0,  # Aumentar de 30 para 60 segundos
)

# Para OpenAI
client = openai.AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=60.0,
)
```

---

### 🟡 IA não entende intenções corretamente

**Sintomas**: Cliente pede agendamento mas IA não reconhece

**Diagnóstico**:

```bash
# Ver resposta completa da IA nos logs
docker compose logs backend | grep -A 50 "LLM Response"
```

**Solução**:

```python
# Melhorar prompt em app/services/conversation_manager.py

SYSTEM_PROMPT = """
Você é um assistente de agendamentos inteligente.

IMPORTANTE:
- Sempre identifique a intenção: AGENDAR, CANCELAR, CONSULTAR
- Pergunte informações faltantes uma de cada vez
- Seja objetivo e claro
- Use formato de data brasileiro (DD/MM/AAAA)

INTENÇÕES:
- AGENDAR: "quero agendar", "marcar consulta", "preciso de horário"
- CANCELAR: "cancelar agendamento", "desmarcar consulta"
- CONSULTAR: "ver meus agendamentos", "quando é minha consulta"

INFORMAÇÕES NECESSÁRIAS:
Para agendamento:
1. Serviço desejado
2. Data preferencial
3. Horário preferencial
4. Nome completo
5. Confirmação final
"""
```

---

## Problemas de Autenticação

### 🔴 Login retorna "Invalid credentials"

**Sintomas**: Usuário e senha corretos mas não consegue logar

**Diagnóstico**:

```sql
-- 1. Verificar se usuário existe
SELECT id, email, full_name, role, is_active, tenant_id
FROM users
WHERE email = 'admin@example.com';

-- 2. Verificar se está ativo
-- 3. Verificar tenant_id correto
```

**Solução**:

```sql
-- Opção 1: Ativar usuário
UPDATE users
SET is_active = true
WHERE email = 'admin@example.com';

-- Opção 2: Resetar senha
-- Gerar novo hash (bcrypt)
UPDATE users
SET hashed_password = '$2b$12$NovoHashAqui',
    updated_at = NOW()
WHERE email = 'admin@example.com';

-- Opção 3: Verificar tenant_id no login
-- Incluir tenant_id correto na requisição
```

**Teste**:

```bash
curl -X POST "https://api.seudominio.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SenhaCorreta123",
    "tenant_id": 1
  }'
```

---

### 🟡 Token JWT expirado

**Sintomas**: 401 Unauthorized após algum tempo logado

**Causa**: Token de acesso expirou (padrão: 7 dias)

**Solução**:

```bash
# Usar refresh token para obter novo access token
curl -X POST "https://api.seudominio.com/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'

# Resposta: novo access_token
```

**Configurar tempo de expiração** (.env):

```bash
# Aumentar tempo de expiração (em minutos)
ACCESS_TOKEN_EXPIRE_MINUTES=10080    # 7 dias
REFRESH_TOKEN_EXPIRE_MINUTES=43200   # 30 dias
```

---

## Problemas de Performance

### 🟡 API lenta / Timeout

**Sintomas**: Requisições demoram mais de 5 segundos

**Diagnóstico**:

```bash
# 1. Ver uso de recursos
docker stats

# 2. Ver conexões do banco
docker compose exec backend psql $DATABASE_URL -c "
  SELECT count(*), state
  FROM pg_stat_activity
  GROUP BY state;
"

# 3. Ver queries lentas
docker compose exec backend psql $DATABASE_URL -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query
  FROM pg_stat_activity
  WHERE state = 'active'
  ORDER BY duration DESC;
"
```

**Solução**:

```bash
# Opção 1: Adicionar índices no banco
docker compose exec backend psql $DATABASE_URL

CREATE INDEX idx_appointments_tenant_date
ON appointments(tenant_id, appointment_date);

CREATE INDEX idx_customers_phone
ON customers(phone);

CREATE INDEX idx_conversations_tenant_customer
ON conversations(tenant_id, customer_id);

# Opção 2: Reduzir pool de conexões
# Editar app/database.py
pool_size=5
max_overflow=5

# Opção 3: Habilitar cache Redis
# .env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# Opção 4: Aumentar recursos do container
# docker-compose.yml
resources:
  limits:
    cpus: '2'
    memory: 2G
```

---

## Problemas com Docker

### 🔴 Container não inicia

**Sintomas**: `docker compose up` falha

**Diagnóstico**:

```bash
# Ver logs
docker compose logs backend

# Ver status dos containers
docker compose ps

# Ver erros de build
docker compose build --no-cache
```

**Soluções Comuns**:

```bash
# Porta já em uso
# Mudar porta no docker-compose.yml ou matar processo
lsof -ti:8000 | xargs kill -9

# Falta de espaço em disco
df -h
docker system prune -a

# Problemas com volumes
docker compose down -v
docker compose up -d

# Rebuild completo
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## Problemas Gerais

### 🟡 CORS Error no Frontend

**Sintomas**: Browser bloqueia requisição por CORS

**Solução**:

```bash
# Adicionar origin no .env
CORS_ORIGINS=["https://seusite.com","http://localhost:3000"]

# Reiniciar
docker compose restart backend
```

---

### 🟡 Logs muito grandes

**Sintomas**: Disco cheio devido a logs

**Solução**:

```bash
# Limpar logs do Docker
docker logs backend 2>/dev/null | tail -1000 > backend.log
docker compose restart backend

# Configurar rotação de logs
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Como Debugar

### Passo a Passo de Debug

```bash
# 1. Ver logs em tempo real
docker compose logs -f backend

# 2. Filtrar logs por erro
docker compose logs backend | grep -i error

# 3. Acessar container
docker compose exec backend bash

# Dentro do container:
# - Ver variáveis de ambiente
env | grep -i api

# - Testar conexão com banco
psql $DATABASE_URL -c "SELECT 1"

# - Rodar Python interativo
python
>>> from app.config import settings
>>> print(settings.DATABASE_URL)

# 4. Testar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs

# 5. Ver todas as variáveis de ambiente
docker compose exec backend env

# 6. Verificar arquivos
docker compose exec backend ls -la /app
```

---

## Quando Pedir Ajuda

Se você já:
- ✅ Consultou este guia de troubleshooting
- ✅ Verificou os logs (`docker compose logs`)
- ✅ Testou os endpoints básicos (`/health`, `/docs`)
- ✅ Consultou a documentação da API
- ✅ Tentou as soluções sugeridas

**E o problema persiste**, então:

### 1. Colete Informações

```bash
# Informações do sistema
cat > debug_info.txt << EOF
Data: $(date)
Versão: $(cat VERSION 2>/dev/null || echo "N/A")

=== Docker ===
$(docker compose ps)

=== Logs (últimas 100 linhas) ===
$(docker compose logs --tail=100 backend)

=== Health Check ===
$(curl -s http://localhost:8000/health || echo "API não respondeu")

=== Banco de Dados ===
$(docker compose exec backend psql $DATABASE_URL -c "SELECT version()" 2>&1 || echo "Erro ao conectar")

=== Variáveis de Ambiente (seguras) ===
ENVIRONMENT=$(grep ENVIRONMENT .env)
DEBUG=$(grep DEBUG .env)
EOF

cat debug_info.txt
```

### 2. Abra uma Issue no GitHub

Inclua:
- Descrição detalhada do problema
- Passos para reproduzir
- Comportamento esperado vs. atual
- Logs relevantes (sem senhas!)
- Arquivo `debug_info.txt`

### 3. Entre em Contato

- **GitHub Issues**: Para bugs e problemas técnicos
- **Discussões**: Para dúvidas gerais
- **Email**: Para suporte urgente

---

## Checklist Geral de Troubleshooting

Use esta checklist para problemas gerais:

### Configuração
- [ ] Arquivo `.env` existe e está correto
- [ ] Todas as variáveis obrigatórias estão preenchidas
- [ ] DATABASE_URL está correta
- [ ] API Keys são válidas (Anthropic/OpenAI)
- [ ] Google Calendar credenciais são válidas
- [ ] Evolution API está acessível

### Banco de Dados
- [ ] Conexão com PostgreSQL funciona
- [ ] Migrations foram executadas (`alembic current`)
- [ ] Tenant existe e está ativo
- [ ] Usuário admin foi criado

### WhatsApp
- [ ] Instância Evolution API existe
- [ ] WhatsApp está conectado (status = "open")
- [ ] Webhook está configurado corretamente
- [ ] Mensagens chegam no webhook

### Google Calendar
- [ ] Service Account tem permissões
- [ ] Calendar ID está correto
- [ ] Calendário foi compartilhado com Service Account

### IA
- [ ] API Key válida e com créditos
- [ ] Timeout configurado adequadamente
- [ ] Prompts estão corretos

### Infraestrutura
- [ ] Containers estão rodando (`docker compose ps`)
- [ ] Portas não estão em conflito
- [ ] Disco não está cheio
- [ ] Memória RAM suficiente

---

**Última Atualização**: 2024
**Versão**: 1.0.0

Se encontrou a solução para um problema não documentado aqui, contribua abrindo um Pull Request!

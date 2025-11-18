# Guia de Configuração de Cliente - AutoAgenda Pro

Guia completo passo a passo para configurar um novo cliente no AutoAgenda Pro.

## Índice

- [Visão Geral](#visão-geral)
- [Tempo Estimado](#tempo-estimado)
- [Pré-requisitos](#pré-requisitos)
- [Passo 1: Criar Tenant no Banco](#passo-1-criar-tenant-no-banco)
- [Passo 2: Configurar Google Calendar](#passo-2-configurar-google-calendar)
- [Passo 3: Conectar WhatsApp](#passo-3-conectar-whatsapp)
- [Passo 4: Configurar Horários de Atendimento](#passo-4-configurar-horários-de-atendimento)
- [Passo 5: Cadastrar Serviços](#passo-5-cadastrar-serviços)
- [Passo 6: Criar Usuário Admin](#passo-6-criar-usuário-admin)
- [Passo 7: Testar o Sistema](#passo-7-testar-o-sistema)
- [Checklist Final](#checklist-final)
- [Problemas Comuns](#problemas-comuns)

---

## Visão Geral

Este guia orienta você através da configuração completa de um novo cliente (tenant) no AutoAgenda Pro, incluindo:

- ✅ Criação do tenant no banco de dados
- ✅ Integração com Google Calendar
- ✅ Configuração do WhatsApp
- ✅ Definição de horários e serviços
- ✅ Criação de usuário administrador
- ✅ Testes de funcionamento

---

## Tempo Estimado

⏱️ **Tempo total: 30-45 minutos**

- Criação do tenant: 5 min
- Google Calendar: 10-15 min
- WhatsApp: 5-10 min
- Configurações: 10-15 min
- Testes: 5 min

---

## Pré-requisitos

Antes de começar, você precisa ter:

### Do Cliente

- [ ] Nome da empresa/clínica
- [ ] E-mail do administrador
- [ ] Número de WhatsApp Business
- [ ] Conta Google (Gmail) para o Calendar
- [ ] Lista de serviços oferecidos
- [ ] Horários de funcionamento
- [ ] Duração padrão dos atendimentos

### Do Sistema

- [ ] Acesso ao banco de dados (Supabase)
- [ ] Acesso à Evolution API
- [ ] Credenciais do Google Service Account
- [ ] API em produção e funcionando

---

## Passo 1: Criar Tenant no Banco

### 1.1. Conectar ao Banco de Dados

**Opção A: Via Supabase Dashboard**
1. Acesse https://supabase.com
2. Faça login e selecione seu projeto
3. Vá em **SQL Editor**
4. Clique em **New Query**

**Opção B: Via psql**
```bash
psql "postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

### 1.2. Executar SQL de Criação

**Template SQL** (copie e modifique):

```sql
-- ============================================
-- CONFIGURAÇÃO DE NOVO CLIENTE
-- Cliente: [NOME DO CLIENTE]
-- Data: [DATA ATUAL]
-- ============================================

-- 1. CRIAR TENANT
INSERT INTO tenants (
    name,
    slug,
    phone,
    email,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Clínica Exemplo',                    -- Nome da empresa
    'clinica-exemplo',                    -- Slug único (sem espaços, minúsculas)
    '5511999999999',                      -- Telefone WhatsApp (com DDI)
    'contato@clinica-exemplo.com',        -- E-mail do cliente
    true,                                  -- Ativo
    NOW(),
    NOW()
) RETURNING id;

-- ⚠️ ANOTE O ID RETORNADO! Você vai precisar dele.
-- Exemplo: Se retornou '5', use 'tenant_id = 5' nos próximos comandos.
```

**Exemplo com dados reais**:

```sql
-- Cliente: Clínica São Paulo
INSERT INTO tenants (
    name,
    slug,
    phone,
    email,
    is_active,
    created_at,
    updated_at
) VALUES (
    'Clínica São Paulo',
    'clinica-sao-paulo',
    '5511987654321',
    'contato@clinicasp.com.br',
    true,
    NOW(),
    NOW()
) RETURNING id;

-- Resultado: id = 5 (exemplo)
```

### 1.3. Verificar Criação

```sql
-- Conferir se o tenant foi criado
SELECT id, name, slug, phone, email, is_active, created_at
FROM tenants
WHERE slug = 'clinica-sao-paulo';

-- Deve retornar 1 linha com os dados inseridos
```

**✅ Checkpoint**: Você deve ter o **tenant_id** anotado (exemplo: 5)

---

## Passo 2: Configurar Google Calendar

### 2.1. Cliente: Criar Google Calendar Dedicado

Instrua o cliente a:

1. Acessar https://calendar.google.com
2. No lado esquerdo, clicar em **"+"** ao lado de "Outros calendários"
3. Selecionar **"Criar novo calendário"**
4. Preencher:
   - **Nome**: `AutoAgenda - Agendamentos`
   - **Descrição**: `Calendário de agendamentos automáticos do AutoAgenda Pro`
   - **Fuso horário**: `(GMT-03:00) Brasília`
5. Clicar em **"Criar calendário"**

### 2.2. Cliente: Compartilhar Calendar com Service Account

1. No Google Calendar, localizar o calendário criado
2. Clicar nos **3 pontos** ao lado do nome → **"Configurações e compartilhamento"**
3. Rolar até **"Compartilhar com pessoas específicas"**
4. Clicar em **"+ Adicionar pessoas"**
5. Inserir o e-mail da Service Account:
   ```
   autoagenda-calendar@seu-projeto.iam.gserviceaccount.com
   ```
   (Este e-mail está no arquivo JSON da Service Account)
6. Definir permissão: **"Fazer alterações em eventos"**
7. **Desmarcar** "Enviar convite por e-mail"
8. Clicar em **"Enviar"**

### 2.3. Cliente: Obter Calendar ID

1. Ainda nas configurações do calendário
2. Rolar até **"Integrar calendário"**
3. Copiar o **ID do calendário**
   - Formato: `abc123@group.calendar.google.com`
   - OU o e-mail pessoal se for o calendário principal: `usuario@gmail.com`

### 2.4. Salvar Calendar ID no Banco

```sql
-- Substituir [TENANT_ID] pelo ID do passo 1
-- Substituir [CALENDAR_ID] pelo ID copiado

INSERT INTO business_config (
    tenant_id,
    google_calendar_id,
    timezone,
    default_appointment_duration,
    created_at,
    updated_at
) VALUES (
    5,                                              -- TENANT_ID do passo 1
    'abc123xyz@group.calendar.google.com',         -- Calendar ID
    'America/Sao_Paulo',
    60,                                             -- 60 minutos (padrão)
    NOW(),
    NOW()
);
```

### 2.5. Verificar Configuração

```sql
-- Conferir configuração
SELECT
    bc.id,
    t.name as tenant_name,
    bc.google_calendar_id,
    bc.timezone,
    bc.default_appointment_duration
FROM business_config bc
JOIN tenants t ON t.id = bc.tenant_id
WHERE bc.tenant_id = 5;  -- Seu tenant_id

-- Deve retornar 1 linha com o calendar_id preenchido
```

**✅ Checkpoint**: Calendar ID salvo no banco de dados

---

## Passo 3: Conectar WhatsApp

### 3.1. Criar Instância no Evolution API

**Via API**:

```bash
curl -X POST 'https://evolution.seudominio.com/instance/create' \
  -H 'apikey: SUA-CHAVE-GLOBAL-EVOLUTION' \
  -H 'Content-Type: application/json' \
  -d '{
    "instanceName": "clinica-sao-paulo",
    "token": "token-seguro-clinica-sp-2024",
    "qrcode": true,
    "webhook": {
      "url": "https://api.seudominio.com/api/v1/webhooks/whatsapp",
      "events": [
        "messages.upsert",
        "connection.update"
      ]
    }
  }'
```

**Resposta esperada**:
```json
{
  "instance": {
    "instanceName": "clinica-sao-paulo",
    "status": "created"
  },
  "hash": {
    "apikey": "token-seguro-clinica-sp-2024"
  }
}
```

### 3.2. Obter QR Code para Conexão

**Opção A: Via API**:
```bash
curl -X GET 'https://evolution.seudominio.com/instance/connect/clinica-sao-paulo' \
  -H 'apikey: SUA-CHAVE-GLOBAL-EVOLUTION'
```

**Opção B: Via Evolution API Manager** (se disponível):
1. Acessar o painel Evolution API
2. Localizar instância `clinica-sao-paulo`
3. Clicar em **"Connect"** ou **"Get QR Code"**

### 3.3. Cliente: Escanear QR Code

1. Enviar imagem do QR Code para o cliente
2. Cliente deve:
   - Abrir WhatsApp no celular
   - Ir em **Configurações** → **Aparelhos conectados**
   - Tocar em **"Conectar um aparelho"**
   - Escanear o QR Code
   - Aguardar confirmação

### 3.4. Verificar Conexão

```bash
curl -X GET 'https://evolution.seudominio.com/instance/connectionState/clinica-sao-paulo' \
  -H 'apikey: SUA-CHAVE-GLOBAL-EVOLUTION'
```

**Resposta esperada**:
```json
{
  "instance": "clinica-sao-paulo",
  "state": "open"
}
```

### 3.5. Salvar Configuração no Banco

```sql
-- Atualizar tenant com informações do WhatsApp
UPDATE tenants
SET
    whatsapp_instance = 'clinica-sao-paulo',
    whatsapp_connected = true,
    updated_at = NOW()
WHERE id = 5;  -- Seu tenant_id
```

### 3.6. Testar Envio de Mensagem

```bash
curl -X POST 'https://evolution.seudominio.com/message/sendText/clinica-sao-paulo' \
  -H 'apikey: SUA-CHAVE-GLOBAL-EVOLUTION' \
  -H 'Content-Type: application/json' \
  -d '{
    "number": "5511987654321",
    "text": "🤖 AutoAgenda Pro conectado com sucesso! Sistema pronto para receber agendamentos."
  }'
```

**✅ Checkpoint**: WhatsApp conectado e enviando mensagens

---

## Passo 4: Configurar Horários de Atendimento

### 4.1. Definir Horários Padrão

**Template SQL**:

```sql
-- Configurar horários de funcionamento
-- Substituir [TENANT_ID] pelo ID do tenant

-- Segunda a Sexta: 8h às 18h
UPDATE business_config
SET
    business_hours = '{
        "monday": {"start": "08:00", "end": "18:00", "enabled": true},
        "tuesday": {"start": "08:00", "end": "18:00", "enabled": true},
        "wednesday": {"start": "08:00", "end": "18:00", "enabled": true},
        "thursday": {"start": "08:00", "end": "18:00", "enabled": true},
        "friday": {"start": "08:00", "end": "18:00", "enabled": true},
        "saturday": {"start": "08:00", "end": "12:00", "enabled": true},
        "sunday": {"start": "00:00", "end": "00:00", "enabled": false}
    }'::jsonb,
    updated_at = NOW()
WHERE tenant_id = 5;  -- Seu tenant_id
```

### 4.2. Configurar Intervalos (Almoço)

```sql
-- Adicionar intervalo de almoço (12h às 13h)
UPDATE business_config
SET
    lunch_break = '{
        "start": "12:00",
        "end": "13:00",
        "enabled": true,
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    }'::jsonb,
    updated_at = NOW()
WHERE tenant_id = 5;
```

### 4.3. Configurar Mensagens Automáticas

```sql
-- Mensagens do sistema
UPDATE business_config
SET
    auto_messages = '{
        "greeting": "Olá! Bem-vindo à Clínica São Paulo. Como posso ajudar você hoje?",
        "appointment_confirmed": "✅ Agendamento confirmado para {date} às {time}. Te esperamos!",
        "appointment_cancelled": "❌ Seu agendamento foi cancelado com sucesso.",
        "outside_hours": "Desculpe, estamos fora do horário de atendimento. Nosso horário é de segunda a sexta, das 8h às 18h, e aos sábados das 8h às 12h.",
        "appointment_reminder": "🔔 Lembrete: Você tem um agendamento amanhã às {time} na Clínica São Paulo."
    }'::jsonb,
    updated_at = NOW()
WHERE tenant_id = 5;
```

### 4.4. Verificar Configurações

```sql
SELECT
    tenant_id,
    business_hours,
    lunch_break,
    auto_messages,
    default_appointment_duration
FROM business_config
WHERE tenant_id = 5;
```

**✅ Checkpoint**: Horários configurados corretamente

---

## Passo 5: Cadastrar Serviços

### 5.1. Inserir Serviços do Cliente

**Template SQL**:

```sql
-- Inserir serviços oferecidos
-- Substituir [TENANT_ID] pelo ID do tenant

INSERT INTO services (tenant_id, name, description, duration_minutes, price, is_active, created_at, updated_at)
VALUES
    -- Serviço 1
    (5, 'Consulta Médica', 'Consulta médica geral', 30, 150.00, true, NOW(), NOW()),

    -- Serviço 2
    (5, 'Retorno', 'Consulta de retorno', 20, 80.00, true, NOW(), NOW()),

    -- Serviço 3
    (5, 'Exames', 'Realização de exames', 45, 200.00, true, NOW(), NOW());
```

**Exemplo completo para clínica**:

```sql
-- Clínica São Paulo - Serviços
INSERT INTO services (tenant_id, name, description, duration_minutes, price, is_active, created_at, updated_at)
VALUES
    (5, 'Consulta Clínico Geral', 'Consulta com clínico geral', 30, 180.00, true, NOW(), NOW()),
    (5, 'Consulta Cardiologista', 'Consulta com especialista em cardiologia', 45, 350.00, true, NOW(), NOW()),
    (5, 'Consulta Dermatologista', 'Consulta com dermatologista', 30, 280.00, true, NOW(), NOW()),
    (5, 'Retorno (até 30 dias)', 'Consulta de retorno', 20, 100.00, true, NOW(), NOW()),
    (5, 'Eletrocardiograma', 'Exame de eletrocardiograma', 20, 80.00, true, NOW(), NOW()),
    (5, 'Holter 24h', 'Monitoramento cardíaco 24 horas', 15, 450.00, true, NOW(), NOW());
```

### 5.2. Verificar Serviços Cadastrados

```sql
-- Listar todos os serviços do tenant
SELECT
    s.id,
    s.name,
    s.description,
    s.duration_minutes,
    s.price,
    s.is_active,
    t.name as tenant_name
FROM services s
JOIN tenants t ON t.id = s.tenant_id
WHERE s.tenant_id = 5
ORDER BY s.name;
```

### 5.3. Desabilitar Serviço (se necessário)

```sql
-- Desabilitar um serviço sem deletá-lo
UPDATE services
SET
    is_active = false,
    updated_at = NOW()
WHERE id = 15 AND tenant_id = 5;  -- ID do serviço específico
```

**✅ Checkpoint**: Serviços cadastrados e ativos

---

## Passo 6: Criar Usuário Admin

### 6.1. Gerar Hash de Senha

**Opção A: Via Python**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("SenhaSegura123!")
print(hashed)
```

**Opção B: Via API** (endpoint helper):
```bash
curl -X POST 'https://api.seudominio.com/api/v1/utils/hash-password' \
  -H 'Content-Type: application/json' \
  -d '{"password": "SenhaSegura123!"}'
```

**Opção C: Online** (use com cuidado):
- https://bcrypt-generator.com/
- Rounds: 12

### 6.2. Criar Usuário no Banco

```sql
-- Criar usuário administrador
-- IMPORTANTE: Trocar o hash pela senha gerada no passo anterior

INSERT INTO users (
    tenant_id,
    email,
    full_name,
    hashed_password,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    5,                                              -- tenant_id
    'admin@clinicasp.com.br',                      -- E-mail do admin
    'Dr. João Silva',                               -- Nome completo
    '$2b$12$...',                                   -- Hash da senha (substituir)
    'admin',                                        -- Role: admin
    true,
    NOW(),
    NOW()
) RETURNING id;
```

**Exemplo completo**:

```sql
INSERT INTO users (
    tenant_id,
    email,
    full_name,
    hashed_password,
    role,
    is_active,
    created_at,
    updated_at
) VALUES (
    5,
    'admin@clinicasp.com.br',
    'Dr. João Silva',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5koiyUCeml6MG',  -- Senha: Admin123!
    'admin',
    true,
    NOW(),
    NOW()
);

-- ⚠️ IMPORTANTE: Enviar as credenciais para o cliente de forma segura!
-- E-mail: admin@clinicasp.com.br
-- Senha: Admin123!
-- INSTRUA O CLIENTE A TROCAR A SENHA NO PRIMEIRO LOGIN!
```

### 6.3. Verificar Usuário Criado

```sql
SELECT
    u.id,
    u.email,
    u.full_name,
    u.role,
    u.is_active,
    t.name as tenant_name
FROM users u
JOIN tenants t ON t.id = u.tenant_id
WHERE u.tenant_id = 5;
```

### 6.4. Testar Login via API

```bash
curl -X POST 'https://api.seudominio.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@clinicasp.com.br",
    "password": "Admin123!",
    "tenant_id": 5
  }'
```

**Resposta esperada**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 10,
    "email": "admin@clinicasp.com.br",
    "full_name": "Dr. João Silva",
    "role": "admin"
  }
}
```

**✅ Checkpoint**: Usuário admin criado e consegue fazer login

---

## Passo 7: Testar o Sistema

### 7.1. Teste de Agendamento via WhatsApp

1. **Enviar mensagem de teste** para o WhatsApp do cliente:
   ```
   Olá, gostaria de agendar uma consulta
   ```

2. **Aguardar resposta da IA** (deve solicitar informações)

3. **Continuar conversa**:
   ```
   Quero consulta com cardiologista para amanhã às 14h
   ```

4. **Conferir se agendamento foi criado**:
   ```sql
   SELECT
       a.id,
       a.appointment_date,
       a.status,
       c.name as customer_name,
       c.phone,
       s.name as service_name
   FROM appointments a
   JOIN customers c ON c.id = a.customer_id
   JOIN services s ON s.id = a.service_id
   WHERE a.tenant_id = 5
   ORDER BY a.created_at DESC
   LIMIT 5;
   ```

### 7.2. Verificar Google Calendar

1. Cliente acessa Google Calendar
2. Verifica se o evento foi criado automaticamente
3. Confirma horário, título e descrição

### 7.3. Teste de Mensagem de Confirmação

O cliente deve receber automaticamente:
```
✅ Agendamento confirmado para [DATA] às [HORA]. Te esperamos!
```

### 7.4. Teste de Cancelamento

```
Preciso cancelar meu agendamento de amanhã
```

Verificar:
- Mensagem de confirmação de cancelamento
- Status no banco mudou para "cancelled"
- Evento removido do Google Calendar

### 7.5. Teste Fora do Horário

Enviar mensagem fora do horário de atendimento:
```
Olá, gostaria de agendar
```

Deve receber:
```
Desculpe, estamos fora do horário de atendimento. Nosso horário é...
```

**✅ Checkpoint**: Todos os testes passaram com sucesso!

---

## Checklist Final

Use esta checklist para garantir que tudo foi configurado:

### Banco de Dados
- [ ] Tenant criado com sucesso
- [ ] Tenant ID anotado
- [ ] Business config criada
- [ ] Horários de funcionamento configurados
- [ ] Serviços cadastrados (mínimo 3)
- [ ] Usuário admin criado
- [ ] Login do admin testado e funcionando

### Google Calendar
- [ ] Cliente criou calendário dedicado
- [ ] Calendário compartilhado com Service Account
- [ ] Calendar ID obtido e salvo no banco
- [ ] Permissão "Fazer alterações" concedida
- [ ] Teste de criação de evento realizado

### WhatsApp
- [ ] Instância Evolution API criada
- [ ] QR Code gerado
- [ ] Cliente escaneou QR Code
- [ ] Status da conexão = "open"
- [ ] Webhook configurado corretamente
- [ ] Teste de envio de mensagem realizado
- [ ] Teste de recebimento de mensagem realizado

### Testes Funcionais
- [ ] Agendamento via WhatsApp funcionando
- [ ] Evento criado no Google Calendar
- [ ] Mensagem de confirmação enviada
- [ ] Cancelamento funcionando
- [ ] Mensagem fora de horário funcionando
- [ ] Cliente satisfeito com configuração

### Documentação
- [ ] Credenciais do admin enviadas ao cliente (com segurança)
- [ ] Cliente orientado a trocar senha
- [ ] Documentação da API compartilhada
- [ ] Suporte técnico informado ao cliente

---

## Problemas Comuns

### ❌ Tenant não foi criado

**Sintoma**: Erro ao inserir tenant

**Solução**:
```sql
-- Verificar se slug já existe
SELECT * FROM tenants WHERE slug = 'seu-slug';

-- Se existir, use outro slug único
```

---

### ❌ Google Calendar não sincroniza

**Sintoma**: Eventos não aparecem no Calendar

**Possíveis causas**:
1. **Calendar ID incorreto**
   ```sql
   -- Verificar Calendar ID salvo
   SELECT google_calendar_id FROM business_config WHERE tenant_id = 5;
   ```

2. **Service Account sem permissão**
   - Cliente precisa compartilhar calendário
   - Permissão deve ser "Fazer alterações em eventos"

3. **Credenciais inválidas**
   - Verificar se `GOOGLE_CALENDAR_CREDENTIALS` está correto no `.env`

**Solução**:
```bash
# Testar criação manual de evento
curl -X POST 'https://api.seudominio.com/api/v1/calendar/test' \
  -H 'Authorization: Bearer [TOKEN]' \
  -H 'Content-Type: application/json' \
  -d '{
    "calendar_id": "abc123@group.calendar.google.com",
    "summary": "Teste",
    "start_time": "2024-12-20T14:00:00",
    "end_time": "2024-12-20T15:00:00"
  }'
```

---

### ❌ WhatsApp não conecta

**Sintoma**: QR Code não funciona ou conexão cai

**Soluções**:

1. **QR Code expirado**:
   ```bash
   # Gerar novo QR Code
   curl -X GET 'https://evolution.seudominio.com/instance/connect/nome-instancia' \
     -H 'apikey: SUA-CHAVE'
   ```

2. **Instância não existe**:
   ```bash
   # Listar instâncias
   curl -X GET 'https://evolution.seudominio.com/instance/fetchInstances' \
     -H 'apikey: SUA-CHAVE'
   ```

3. **Webhook incorreto**:
   ```bash
   # Atualizar webhook
   curl -X PUT 'https://evolution.seudominio.com/webhook/set/nome-instancia' \
     -H 'apikey: SUA-CHAVE' \
     -H 'Content-Type: application/json' \
     -d '{
       "url": "https://api.seudominio.com/api/v1/webhooks/whatsapp",
       "events": ["messages.upsert"]
     }'
   ```

---

### ❌ IA não responde mensagens

**Sintoma**: WhatsApp recebe mensagens mas não responde

**Verificações**:

1. **Webhook chegando?**
   ```bash
   # Ver logs da API
   docker compose logs -f backend | grep webhook
   ```

2. **API Key da IA válida?**
   ```bash
   # Testar Anthropic API
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "claude-3-5-sonnet-20241022",
       "max_tokens": 100,
       "messages": [{"role": "user", "content": "Hi"}]
     }'
   ```

3. **Tenant ativo?**
   ```sql
   SELECT is_active FROM tenants WHERE id = 5;
   -- Deve retornar: true
   ```

---

### ❌ Login não funciona

**Sintoma**: Erro 401 ou credenciais inválidas

**Soluções**:

1. **Verificar senha hash**:
   ```sql
   SELECT email, hashed_password FROM users WHERE email = 'admin@example.com';
   ```

2. **Verificar tenant_id**:
   ```bash
   # Incluir tenant_id correto no login
   curl -X POST 'https://api.seudominio.com/api/v1/auth/login' \
     -H 'Content-Type: application/json' \
     -d '{
       "email": "admin@example.com",
       "password": "senha",
       "tenant_id": 5
     }'
   ```

3. **Usuário inativo**:
   ```sql
   UPDATE users SET is_active = true WHERE email = 'admin@example.com';
   ```

---

## Suporte Adicional

Se após seguir este guia você ainda tiver problemas:

1. **Consulte**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Verifique logs**: `docker compose logs -f backend`
3. **Teste endpoints**: Swagger em `/docs`
4. **Abra issue**: GitHub Issues do projeto

---

## Próximos Passos

Após configuração bem-sucedida:

1. ✅ **Treinar cliente** no uso do sistema
2. ✅ **Configurar lembretes** automáticos (opcional)
3. ✅ **Personalizar mensagens** da IA
4. ✅ **Adicionar mais usuários** se necessário
5. ✅ **Monitorar métricas** de agendamentos

---

**Configuração concluída! 🎉**

O AutoAgenda Pro está pronto para automatizar os agendamentos do cliente via WhatsApp.

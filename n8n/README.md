# 🔄 N8N Workflows Documentation

## Overview

N8N is used for workflow automation in AutoAgenda Pro, handling complex business logic and integrations between different services.

## Workflows

### 1. WhatsApp Message Processing

**Trigger**: Webhook from Evolution API
**Purpose**: Process incoming WhatsApp messages and trigger appropriate responses

**Flow**:
1. Receive webhook from Evolution API
2. Extract message content and sender info
3. Check if user exists in database
4. Create or update user record
5. Send to Claude AI for processing
6. Execute appropriate action (create appointment, send response, etc.)

**Webhook URL**: `https://your-n8n-instance.com/webhook/whatsapp-incoming`

### 2. Appointment Reminder

**Trigger**: Schedule (daily at 8 AM)
**Purpose**: Send appointment reminders via WhatsApp

**Flow**:
1. Query database for appointments in next 24 hours
2. For each appointment:
   - Format reminder message
   - Send via Evolution API
   - Log reminder sent

### 3. Calendar Sync

**Trigger**: Schedule (every 15 minutes)
**Purpose**: Sync Google Calendar events with database

**Flow**:
1. Fetch recent calendar events from Google Calendar
2. Compare with database records
3. Update/create appointment records
4. Send notifications for new/changed appointments

### 4. Conversation Context Management

**Trigger**: After each conversation
**Purpose**: Maintain conversation history and context

**Flow**:
1. Store conversation messages
2. Analyze conversation for key information
3. Update user preferences
4. Close inactive sessions after timeout

## Setup Instructions

### 1. Install N8N

#### Using Docker (Recommended)

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

#### Using npm

```bash
npm install n8n -g
n8n start
```

### 2. Configure Credentials

In N8N UI (http://localhost:5678):

1. **PostgreSQL Credentials**
   - Host: Your Supabase host
   - Database: postgres
   - User: postgres
   - Password: Your Supabase password
   - SSL: Enable

2. **HTTP Request (Evolution API)**
   - Authentication: Header Auth
   - Name: apikey
   - Value: Your Evolution API key

3. **HTTP Request (Claude AI)**
   - Authentication: Header Auth
   - Name: x-api-key
   - Value: Your Anthropic API key

4. **Google Calendar**
   - Use OAuth2 authentication
   - Scopes: https://www.googleapis.com/auth/calendar

### 3. Import Workflows

Workflow JSON files will be provided in this directory. To import:

1. Open N8N UI
2. Click "Import from File"
3. Select the workflow JSON file
4. Configure credentials
5. Activate the workflow

## Workflow Templates

### WhatsApp Incoming Message Workflow

```json
{
  "name": "WhatsApp Message Processor",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "path": "whatsapp-incoming",
        "responseMode": "lastNode"
      }
    },
    {
      "name": "Extract Message Data",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "phone",
              "value": "={{$json.data.key.remoteJid}}"
            },
            {
              "name": "message",
              "value": "={{$json.data.message.conversation}}"
            }
          ]
        }
      }
    }
  ]
}
```

## Webhook URLs

Configure these webhook URLs in your services:

| Service | Webhook URL | Purpose |
|---------|-------------|---------|
| Evolution API | `/webhook/whatsapp-incoming` | Incoming messages |
| Google Calendar | `/webhook/calendar-update` | Calendar changes |
| Backend API | `/webhook/appointment-created` | New appointments |

## Environment Variables for N8N

Add to your N8N environment:

```bash
# Database
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=your-supabase-host
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=postgres
DB_POSTGRESDB_USER=postgres
DB_POSTGRESDB_PASSWORD=your-password

# Timezone
GENERIC_TIMEZONE=America/Sao_Paulo

# Webhook URL
WEBHOOK_URL=https://your-n8n-instance.com/
```

## Common Workflow Patterns

### 1. Error Handling

Always include error handling nodes:

```
Main Node → Error Trigger → Log Error → Notify Admin
```

### 2. Rate Limiting

For API calls, add function nodes to implement delays:

```javascript
// Wait 1 second between API calls
return new Promise((resolve) => {
  setTimeout(() => resolve(items), 1000);
});
```

### 3. Data Validation

Use function nodes to validate data before processing:

```javascript
const item = items[0].json;

// Validate phone number
if (!item.phone || !item.phone.match(/^\d{10,15}$/)) {
  throw new Error('Invalid phone number');
}

// Validate message
if (!item.message || item.message.trim().length === 0) {
  throw new Error('Empty message');
}

return items;
```

## Monitoring and Debugging

### Enable Execution Logging

In N8N settings:
```bash
N8N_LOG_LEVEL=debug
N8N_LOG_OUTPUT=console,file
```

### View Execution History

1. Go to Executions tab in N8N UI
2. Filter by workflow name
3. Click execution to see details
4. Review node outputs and errors

### Common Issues

| Issue | Solution |
|-------|----------|
| Webhook not triggered | Check webhook URL and Evolution API configuration |
| Database connection failed | Verify Supabase credentials and whitelist N8N IP |
| API rate limit exceeded | Implement delays between requests |
| Timeout errors | Increase workflow timeout in settings |

## Best Practices

1. **Use descriptive node names** for easy debugging
2. **Implement error handling** for all critical paths
3. **Add logging nodes** to track workflow progress
4. **Test workflows** with sample data before activation
5. **Monitor execution history** regularly
6. **Keep workflows modular** for reusability
7. **Document custom functions** with comments
8. **Use environment variables** for configuration

## Scaling Considerations

For production environments:

1. **Use N8N in queue mode** for better performance
2. **Deploy multiple N8N instances** behind load balancer
3. **Use external database** instead of SQLite
4. **Implement retry mechanisms** for failed executions
5. **Monitor resource usage** and scale accordingly

## Integration with FastAPI Backend

### Calling N8N Webhooks from Backend

```python
import httpx
from app.config import settings

async def trigger_n8n_workflow(workflow_name: str, data: dict):
    """Trigger N8N workflow via webhook."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.N8N_WEBHOOK_URL}/webhook/{workflow_name}",
            json=data,
            timeout=30.0
        )
        return response.json()
```

### Calling Backend API from N8N

Use HTTP Request node with:
- Method: POST
- URL: `http://backend:8000/api/v1/endpoint`
- Authentication: Bearer Token
- Headers: `Content-Type: application/json`

## Additional Resources

- [N8N Documentation](https://docs.n8n.io/)
- [N8N Community](https://community.n8n.io/)
- [Workflow Templates](https://n8n.io/workflows)
- [N8N YouTube Channel](https://www.youtube.com/c/n8n-io)

## Workflow Maintenance

### Backup Workflows

```bash
# Export all workflows
n8n export:workflow --all --output=./workflows-backup/

# Import workflows
n8n import:workflow --input=./workflows-backup/
```

### Update Workflows

1. Make changes in N8N UI
2. Test with sample data
3. Export updated workflow
4. Commit to version control
5. Deploy to production

## Support

For N8N-specific issues:
- Check [N8N Documentation](https://docs.n8n.io/)
- Visit [N8N Community Forum](https://community.n8n.io/)
- Open issue in this repository for AutoAgenda-specific problems

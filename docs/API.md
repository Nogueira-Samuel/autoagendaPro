# AutoAgenda Pro API Documentation

Complete REST API reference for AutoAgenda Pro - AI-powered WhatsApp appointment scheduling system.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Appointments](#appointments-endpoints)
  - [Customers](#customers-endpoints)
  - [Webhooks](#webhooks-endpoints)

---

## Overview

AutoAgenda Pro provides a RESTful API for managing appointments, customers, and WhatsApp integrations. All endpoints return JSON responses and use standard HTTP response codes.

**Version**: 0.1.0
**Protocol**: HTTPS
**Data Format**: JSON

## Base URL

```
Production:  https://api.autoagenda.com/api/v1
Development: http://localhost:8000/api/v1
```

All endpoints are prefixed with `/api/v1`.

## Authentication

The API uses JWT (JSON Web Token) bearer authentication.

### Obtaining a Token

**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "yourpassword",
  "tenant_id": 1
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "tenant_id": 1
  }
}
```

### Using the Token

Include the access token in the `Authorization` header for all authenticated requests:

```http
GET /api/v1/appointments
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Expiration

- **Access Token**: 7 days
- **Refresh Token**: 7 days

Use the refresh token to obtain a new access token without re-authenticating.

## Error Handling

### Error Response Format

```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400,
  "details": []
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Validation Errors

```json
{
  "error": true,
  "message": "Validation error",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse.

**Limits**:
- 100 requests per minute per IP address
- 1000 requests per hour per user

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
```

When rate limit is exceeded:
```json
{
  "error": true,
  "message": "Rate limit exceeded. Maximum 100 requests per 60 seconds.",
  "status_code": 429
}
```

---

## Endpoints

## Authentication Endpoints

### Register User

Create a new user account.

**Endpoint:** `POST /auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 5,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": 1,
  "is_active": true,
  "last_login": null,
  "created_at": "2025-11-17T10:30:00Z",
  "updated_at": "2025-11-17T10:30:00Z"
}
```

**Validation Rules:**
- `email`: Valid email format, unique per tenant
- `password`: Minimum 8 characters, must contain letter and number
- `role`: One of: `super_admin`, `admin`, `operator`, `viewer`

---

### Login

Authenticate and receive JWT tokens.

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "admin123",
  "tenant_id": 1
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwidGVuYW50X2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3MDA0ODY0MDAsImlhdCI6MTY5OTg4MTYwMH0.xyz",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZXhwIjoxNzAxMDkyNDAwLCJpYXQiOjE2OTk4ODE2MDAsInR5cGUiOiJyZWZyZXNoIn0.abc",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "tenant_id": 1
  }
}
```

**Errors:**
- `401`: Invalid email or password
- `401`: User account is inactive

---

### Get Current User

Get authenticated user information.

**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "admin@example.com",
  "full_name": "Admin User",
  "role": "admin",
  "tenant_id": 1,
  "is_active": true,
  "last_login": "2025-11-17T10:30:00Z",
  "created_at": "2025-11-17T09:00:00Z",
  "updated_at": "2025-11-17T10:30:00Z"
}
```

---

### Refresh Token

Get new access token using refresh token.

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Appointments Endpoints

### List Appointments

Get all appointments with optional filters.

**Endpoint:** `GET /appointments`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | integer | Yes | Tenant ID for filtering |
| `start_date` | date | No | Filter from date (YYYY-MM-DD) |
| `end_date` | date | No | Filter to date (YYYY-MM-DD) |
| `status` | string | No | Filter by status |
| `customer_id` | integer | No | Filter by customer |
| `skip` | integer | No | Pagination offset (default: 0) |
| `limit` | integer | No | Max records (default: 100, max: 500) |

**Example Request:**
```http
GET /api/v1/appointments?tenant_id=1&start_date=2025-11-17&status=confirmed&limit=50
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "tenant_id": 1,
    "customer_id": 10,
    "service_id": 2,
    "scheduled_date": "2025-11-20",
    "scheduled_time": "14:30:00",
    "duration_minutes": 60,
    "status": "confirmed",
    "notes": "Patient has insurance",
    "google_calendar_event_id": "abc123xyz",
    "cancellation_reason": null,
    "cancelled_by": null,
    "created_at": "2025-11-17T10:00:00Z",
    "updated_at": "2025-11-17T10:00:00Z"
  }
]
```

---

### Get Appointment

Get single appointment by ID.

**Endpoint:** `GET /appointments/{appointment_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "tenant_id": 1,
  "customer_id": 10,
  "service_id": 2,
  "scheduled_date": "2025-11-20",
  "scheduled_time": "14:30:00",
  "duration_minutes": 60,
  "status": "confirmed",
  "notes": "Patient has insurance",
  "google_calendar_event_id": "abc123xyz",
  "cancellation_reason": null,
  "cancelled_by": null,
  "created_at": "2025-11-17T10:00:00Z",
  "updated_at": "2025-11-17T10:00:00Z"
}
```

**Errors:**
- `404`: Appointment not found

---

### Create Appointment

Create new appointment. Automatically creates Google Calendar event.

**Endpoint:** `POST /appointments`

**Request:**
```json
{
  "tenant_id": 1,
  "customer_id": 10,
  "service_id": 2,
  "scheduled_date": "2025-11-20",
  "scheduled_time": "14:30:00",
  "duration_minutes": 60,
  "notes": "Patient has insurance"
}
```

**Response:** `201 Created`
```json
{
  "id": 15,
  "tenant_id": 1,
  "customer_id": 10,
  "service_id": 2,
  "scheduled_date": "2025-11-20",
  "scheduled_time": "14:30:00",
  "duration_minutes": 60,
  "status": "pending",
  "notes": "Patient has insurance",
  "google_calendar_event_id": "gcal_event_abc123",
  "cancellation_reason": null,
  "cancelled_by": null,
  "created_at": "2025-11-17T10:30:00Z",
  "updated_at": "2025-11-17T10:30:00Z"
}
```

---

### Update Appointment

Update existing appointment.

**Endpoint:** `PUT /appointments/{appointment_id}`

**Request:**
```json
{
  "scheduled_date": "2025-11-21",
  "scheduled_time": "15:00:00",
  "notes": "Rescheduled by patient request"
}
```

**Response:** `200 OK`
```json
{
  "id": 15,
  "tenant_id": 1,
  "customer_id": 10,
  "service_id": 2,
  "scheduled_date": "2025-11-21",
  "scheduled_time": "15:00:00",
  "duration_minutes": 60,
  "status": "pending",
  "notes": "Rescheduled by patient request",
  "google_calendar_event_id": "gcal_event_abc123",
  "cancellation_reason": null,
  "cancelled_by": null,
  "created_at": "2025-11-17T10:30:00Z",
  "updated_at": "2025-11-17T11:00:00Z"
}
```

---

### Cancel Appointment

Cancel appointment and delete from Google Calendar.

**Endpoint:** `DELETE /appointments/{appointment_id}`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cancellation_reason` | string | No | Reason for cancellation |
| `cancelled_by` | string | No | Who cancelled (customer/business) |

**Example:**
```http
DELETE /api/v1/appointments/15?cancellation_reason=Patient%20requested&cancelled_by=customer
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "status": "cancelled",
  "appointment_id": 15,
  "cancelled_by": "customer"
}
```

---

## Customers Endpoints

### List Customers

Get all customers with optional search and pagination.

**Endpoint:** `GET /customers`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | integer | Yes | Tenant ID |
| `search` | string | No | Search by name, phone, email |
| `skip` | integer | No | Pagination offset (default: 0) |
| `limit` | integer | No | Max records (default: 100, max: 500) |

**Example:**
```http
GET /api/v1/customers?tenant_id=1&search=silva&limit=20
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 10,
    "tenant_id": 1,
    "name": "João Silva",
    "phone": "5521999999999",
    "email": "joao@example.com",
    "notes": "Preferred afternoon appointments",
    "created_at": "2025-11-10T09:00:00Z",
    "updated_at": "2025-11-10T09:00:00Z"
  }
]
```

---

### Get Customer

Get single customer by ID.

**Endpoint:** `GET /customers/{customer_id}`

**Response:** `200 OK`
```json
{
  "id": 10,
  "tenant_id": 1,
  "name": "João Silva",
  "phone": "5521999999999",
  "email": "joao@example.com",
  "notes": "Preferred afternoon appointments",
  "created_at": "2025-11-10T09:00:00Z",
  "updated_at": "2025-11-10T09:00:00Z"
}
```

---

### Get Customer by Phone

Find customer by phone number (useful for WhatsApp integration).

**Endpoint:** `GET /customers/phone/{phone}`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | integer | Yes | Tenant ID |

**Example:**
```http
GET /api/v1/customers/phone/5521999999999?tenant_id=1
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 10,
  "tenant_id": 1,
  "name": "João Silva",
  "phone": "5521999999999",
  "email": "joao@example.com",
  "notes": "Preferred afternoon appointments",
  "created_at": "2025-11-10T09:00:00Z",
  "updated_at": "2025-11-10T09:00:00Z"
}
```

**Errors:**
- `404`: Customer not found

---

### Get Customer Appointments

Get all appointments for a customer.

**Endpoint:** `GET /customers/{customer_id}/appointments`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `include_cancelled` | boolean | No | Include cancelled (default: false) |
| `skip` | integer | No | Pagination offset |
| `limit` | integer | No | Max records |

**Response:** `200 OK`
```json
{
  "customer_id": 10,
  "total_appointments": 5,
  "appointments": [
    {
      "id": 1,
      "scheduled_date": "2025-11-20",
      "scheduled_time": "14:30:00",
      "status": "confirmed",
      "service_id": 2
    }
  ]
}
```

---

### Create Customer

Create new customer.

**Endpoint:** `POST /customers`

**Request:**
```json
{
  "tenant_id": 1,
  "name": "Maria Santos",
  "phone": "5521988888888",
  "email": "maria@example.com",
  "notes": "Prefers WhatsApp contact"
}
```

**Response:** `201 Created`
```json
{
  "id": 25,
  "tenant_id": 1,
  "name": "Maria Santos",
  "phone": "5521988888888",
  "email": "maria@example.com",
  "notes": "Prefers WhatsApp contact",
  "created_at": "2025-11-17T11:00:00Z",
  "updated_at": "2025-11-17T11:00:00Z"
}
```

**Validation:**
- `phone`: Brazilian format (55 + DDD + number)
- `email`: Valid email format

**Errors:**
- `400`: Customer with phone already exists

---

### Update Customer

Update existing customer.

**Endpoint:** `PUT /customers/{customer_id}`

**Request:**
```json
{
  "email": "maria.santos@example.com",
  "notes": "Updated email address"
}
```

**Response:** `200 OK`
```json
{
  "id": 25,
  "tenant_id": 1,
  "name": "Maria Santos",
  "phone": "5521988888888",
  "email": "maria.santos@example.com",
  "notes": "Updated email address",
  "created_at": "2025-11-17T11:00:00Z",
  "updated_at": "2025-11-17T11:30:00Z"
}
```

---

### Delete Customer

Delete customer (only if no active appointments).

**Endpoint:** `DELETE /customers/{customer_id}`

**Response:** `204 No Content`

**Errors:**
- `400`: Cannot delete customer with active appointments

---

## Webhooks Endpoints

### WhatsApp Message Webhook

Receive WhatsApp messages from Evolution API.

**Endpoint:** `POST /webhooks/whatsapp`

**Request:**
```json
{
  "instance": "clinica-exemplo-test",
  "data": {
    "data": {
      "key": {
        "remoteJid": "5521999999999@s.whatsapp.net"
      },
      "message": {
        "conversation": "Olá, gostaria de agendar uma consulta"
      }
    }
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "processed"
}
```

**Process Flow:**
1. Extract phone number and message
2. Identify tenant by instance name
3. Process with AI (LLM) for intent detection
4. Execute action (create appointment, etc.)
5. Send response back via WhatsApp

**Errors:**
- `404`: Tenant not found for instance
- `500`: Processing failed

---

### WhatsApp Status Webhook

Receive status updates from Evolution API.

**Endpoint:** `POST /webhooks/whatsapp/status`

**Request:**
```json
{
  "instance": "clinica-exemplo-test",
  "event": "message.sent",
  "data": {
    "message_id": "abc123"
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "received"
}
```

---

## Multi-Tenant

All endpoints require `tenant_id` parameter or use tenant from JWT token.

**Methods to specify tenant:**
1. Query parameter: `?tenant_id=1`
2. HTTP header: `X-Tenant-ID: 1`
3. JWT token (user's tenant_id)

**Cross-tenant access is prevented** - users can only access resources within their tenant.

---

## API Versioning

Current version: **v1**

The API version is included in the URL path: `/api/v1/`

Future versions will be released as `/api/v2/`, etc., with backward compatibility maintained.

---

## Support

**Documentation:** https://docs.autoagenda.com
**API Status:** https://status.autoagenda.com
**Support Email:** support@autoagenda.com

---

**Last Updated:** 2025-11-17
**API Version:** 1.0.0

"""
Pydantic Schemas Package

Request/Response validation schemas for AutoAgenda Pro API.
All schemas use Pydantic v2 syntax.
"""

from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.business_config import (
    BusinessConfigCreate,
    BusinessConfigUpdate,
    BusinessConfigResponse,
)
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentCancel,
)
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.webhook import WhatsAppWebhookEvent

__all__ = [
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # BusinessConfig
    "BusinessConfigCreate",
    "BusinessConfigUpdate",
    "BusinessConfigResponse",
    # Service
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    # Appointment
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AppointmentCancel",
    # Conversation
    "ConversationCreate",
    "ConversationResponse",
    # Webhook
    "WhatsAppWebhookEvent",
]

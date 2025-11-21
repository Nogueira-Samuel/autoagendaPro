"""
Database Models Package

Imports all SQLAlchemy models for AutoAgenda Pro multi-tenant system.

IMPORTANT: All models must be imported here for Alembic to detect them
during automatic migration generation.

Models:
    - Tenant: Client businesses using the system
    - User: System users (admins, operators)
    - BusinessConfig: Business-specific configurations
    - Service: Services offered by tenants
    - Customer: End customers who book appointments
    - Appointment: Scheduled appointments
    - Conversation: WhatsApp conversation history
    - NotificationLog: Notification delivery logs
"""

# Import Base first
from app.database import Base

# Import all models in dependency order
from app.models.tenant import Tenant, TenantPlan
from app.models.user import User, UserRole
from app.models.business_config import BusinessConfig
from app.models.service import Service
from app.models.customer import Customer
from app.models.appointment import (
    Appointment,
    AppointmentStatus,
    CancelledBy,
)
from app.models.conversation import (
    Conversation,
    MessageDirection,
    MessageType,
)
from app.models.notification_log import NotificationLog

# Expose all models and enums
__all__ = [
    # Base
    "Base",
    # Models
    "Tenant",
    "User",
    "BusinessConfig",
    "Service",
    "Customer",
    "Appointment",
    "Conversation",
    "NotificationLog",
    # Enums - Tenant
    "TenantPlan",
    # Enums - User
    "UserRole",
    # Enums - Appointment
    "AppointmentStatus",
    "CancelledBy",
    # Enums - Conversation
    "MessageDirection",
    "MessageType",
]

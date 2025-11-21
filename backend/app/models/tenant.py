"""
Tenant Model

Representa um negócio cliente (tenant) no sistema multi-tenant.
Cada tenant tem dados isolados e configurações independentes.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.business_config import BusinessConfig
    from app.models.service import Service
    from app.models.customer import Customer
    from app.models.appointment import Appointment
    from app.models.conversation import Conversation
    from app.models.notification_log import NotificationLog


class TenantPlan(str, enum.Enum):
    """Planos de assinatura disponíveis."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """
    Modelo de Tenant (Cliente do Sistema).

    Representa uma empresa/negócio que usa o AutoAgenda Pro.
    Cada tenant tem dados completamente isolados dos demais.

    Attributes:
        id: Identificador único do tenant
        name: Nome do negócio (ex: "Clínica Dr. Silva")
        slug: Identificador URL-friendly único
        is_active: Indica se o tenant está ativo
        plan: Plano de assinatura do tenant
        google_calendar_credentials: Credenciais da Service Account do Google
        google_calendar_id: ID do calendário do Google a ser usado
        evolution_instance_name: Nome da instância no Evolution API
        evolution_api_key: API key específica da instância (criptografada)
        timezone: Timezone do negócio
        created_at: Data de criação
        updated_at: Data da última atualização
    """

    __tablename__ = "tenants"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome do negócio"
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Identificador único URL-friendly"
    )

    # Status and Plan
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Indica se o tenant está ativo"
    )

    plan: Mapped[TenantPlan] = mapped_column(
        SQLEnum(TenantPlan, name="tenant_plan"),
        default=TenantPlan.FREE,
        nullable=False,
        comment="Plano de assinatura"
    )

    # Google Calendar Integration
    google_calendar_credentials: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Credenciais JSON da Service Account do Google"
    )

    google_calendar_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="ID do calendário do Google Calendar"
    )

    # Evolution API (WhatsApp) Integration
    evolution_instance_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Nome da instância no Evolution API"
    )

    evolution_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="API key da instância Evolution (deve ser criptografada)"
    )

    # Localization
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="America/Sao_Paulo",
        nullable=False,
        comment="Timezone do negócio"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Data de criação do registro"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Data da última atualização"
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    business_config: Mapped["BusinessConfig | None"] = relationship(
        "BusinessConfig",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    customers: Mapped[list["Customer"]] = relationship(
        "Customer",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    notification_logs: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_tenant_slug", "slug"),
        Index("idx_tenant_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}', plan='{self.plan.value}')>"

    @property
    def is_premium(self) -> bool:
        """Verifica se o tenant tem plano premium ou superior."""
        return self.plan in {TenantPlan.PREMIUM, TenantPlan.ENTERPRISE}

    @property
    def has_google_calendar(self) -> bool:
        """Verifica se o tenant tem Google Calendar configurado."""
        return bool(self.google_calendar_credentials and self.google_calendar_id)

    @property
    def has_whatsapp(self) -> bool:
        """Verifica se o tenant tem WhatsApp configurado."""
        return bool(self.evolution_instance_name and self.evolution_api_key)

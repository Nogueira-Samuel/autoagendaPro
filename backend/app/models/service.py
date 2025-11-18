"""
Service Model

Modelo de serviços oferecidos por cada tenant.
Cada tenant pode ter múltiplos serviços com diferentes durações e preços.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.appointment import Appointment


class Service(Base):
    """
    Modelo de Serviço.

    Representa um serviço oferecido por um tenant (ex: consulta, corte de cabelo).
    Cada serviço tem duração, preço, e pode ser ativado/desativado.

    Attributes:
        id: Identificador único do serviço
        tenant_id: ID do tenant que oferece o serviço
        name: Nome do serviço
        description: Descrição detalhada do serviço
        duration_minutes: Duração do serviço em minutos
        price: Preço do serviço (opcional)
        is_active: Indica se o serviço está disponível para agendamento
        color: Cor hexadecimal para exibição no calendário
        created_at: Data de criação
        updated_at: Data da última atualização
    """

    __tablename__ = "services"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Tenant Relationship
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do tenant que oferece o serviço"
    )

    # Service Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome do serviço (ex: Consulta, Corte de Cabelo)"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Descrição detalhada do serviço"
    )

    # Duration and Pricing
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Duração do serviço em minutos"
    )

    price: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
        comment="Preço do serviço (opcional)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Indica se o serviço está disponível para agendamento"
    )

    # Visual
    color: Mapped[str] = mapped_column(
        String(7),
        default="#3B82F6",  # Tailwind blue-500
        nullable=False,
        comment="Cor hexadecimal para exibição no calendário (ex: #FF5733)"
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
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="services",
        lazy="selectin"
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="service",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_service_tenant_id", "tenant_id"),
        Index("idx_service_tenant_active", "tenant_id", "is_active"),
        Index("idx_service_tenant_name", "tenant_id", "name"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return (
            f"<Service(id={self.id}, name='{self.name}', "
            f"duration={self.duration_minutes}min, tenant_id={self.tenant_id})>"
        )

    @property
    def duration_hours(self) -> float:
        """Retorna a duração em horas."""
        return self.duration_minutes / 60

    @property
    def formatted_price(self) -> str:
        """Retorna o preço formatado em reais."""
        if self.price is None:
            return "Preço não definido"
        return f"R$ {self.price:.2f}"

    @property
    def formatted_duration(self) -> str:
        """
        Retorna a duração formatada.

        Returns:
            String formatada (ex: "1h 30min", "45min")
        """
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}min"

    def is_valid_color(self) -> bool:
        """
        Valida se a cor está em formato hexadecimal válido.

        Returns:
            True se válido, False caso contrário
        """
        if not self.color:
            return False

        # Remove # se presente
        color = self.color.lstrip("#")

        # Verifica se tem 6 caracteres hexadecimais
        if len(color) != 6:
            return False

        try:
            int(color, 16)
            return True
        except ValueError:
            return False

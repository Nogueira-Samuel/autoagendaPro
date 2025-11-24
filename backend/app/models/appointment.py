"""
Appointment Model

Modelo de agendamentos.
Representa compromissos agendados por clientes via WhatsApp.
"""

import enum
from datetime import datetime, date, time, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Time,
    ForeignKey,
    Integer,
    Text,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.customer import Customer
    from app.models.service import Service
    from app.models.notification_log import NotificationLog


class AppointmentStatus(str, enum.Enum):
    """Status de um agendamento."""
    PENDING = "pending"          # Aguardando confirmação
    CONFIRMED = "confirmed"      # Confirmado
    CANCELLED = "cancelled"      # Cancelado
    COMPLETED = "completed"      # Realizado
    NO_SHOW = "no_show"         # Cliente não compareceu


class CancelledBy(str, enum.Enum):
    """Quem cancelou o agendamento."""
    CUSTOMER = "customer"        # Cliente cancelou
    BUSINESS = "business"        # Negócio cancelou
    SYSTEM = "system"           # Sistema cancelou (ex: regra automática)


class Appointment(Base):
    """
    Modelo de Agendamento.

    Representa um compromisso agendado por um cliente.
    Integrado com Google Calendar e WhatsApp.

    Attributes:
        id: Identificador único do agendamento
        tenant_id: ID do tenant
        customer_id: ID do cliente
        service_id: ID do serviço
        scheduled_date: Data do agendamento
        scheduled_time: Horário do agendamento
        duration_minutes: Duração em minutos
        status: Status do agendamento
        google_calendar_event_id: ID do evento no Google Calendar
        notes: Observações sobre o agendamento
        cancellation_reason: Motivo do cancelamento
        cancelled_by: Quem cancelou
        reminder_sent: Se lembrete foi enviado
        reminder_sent_at: Quando o lembrete foi enviado
        created_at: Data de criação
        updated_at: Data da última atualização
    """

    __tablename__ = "appointments"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Relationships
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do tenant"
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do cliente"
    )

    service_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID do serviço"
    )

    # Appointment Schedule
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Data do agendamento"
    )

    scheduled_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Horário do agendamento"
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Duração do agendamento em minutos"
    )

    # Status
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status do agendamento"
    )

    # Google Calendar Integration
    google_calendar_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="ID do evento no Google Calendar"
    )

    # Additional Information
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Observações sobre o agendamento"
    )

    # Cancellation
    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Motivo do cancelamento"
    )

    cancelled_by: Mapped[CancelledBy | None] = mapped_column(
        SQLEnum(CancelledBy, name="cancelled_by"),
        nullable=True,
        comment="Quem cancelou o agendamento"
    )

    # Reminders
    reminder_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica se lembrete foi enviado"
    )

    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data/hora do envio do lembrete"
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
        back_populates="appointments",
        lazy="selectin"
    )

    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="appointments",
        lazy="selectin"
    )

    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="appointments",
        lazy="selectin"
    )

    notification_logs: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog",
        back_populates="appointment",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes and Constraints
    __table_args__ = (
        # Evita double booking no mesmo horário
        UniqueConstraint(
            "tenant_id", "scheduled_date", "scheduled_time",
            name="uq_appointment_tenant_datetime"
        ),
        Index("idx_appointment_tenant_id", "tenant_id"),
        Index("idx_appointment_customer_id", "customer_id"),
        Index("idx_appointment_service_id", "service_id"),
        Index("idx_appointment_tenant_date_time", "tenant_id", "scheduled_date", "scheduled_time"),
        Index("idx_appointment_tenant_status", "tenant_id", "status"),
        Index("idx_appointment_scheduled_date", "scheduled_date"),
        Index("idx_appointment_calendar_event_id", "google_calendar_event_id"),
        # Garante que duration_minutes seja positivo
        CheckConstraint("duration_minutes > 0", name="check_duration_positive"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return (
            f"<Appointment(id={self.id}, customer_id={self.customer_id}, "
            f"date={self.scheduled_date}, time={self.scheduled_time}, "
            f"status='{self.status.value}')>"
        )

    @property
    def scheduled_datetime(self) -> datetime:
        """
        Retorna data e hora combinadas do agendamento.

        Returns:
            DateTime combinando scheduled_date e scheduled_time
        """
        return datetime.combine(self.scheduled_date, self.scheduled_time)

    @property
    def end_datetime(self) -> datetime:
        """
        Retorna data/hora do fim do agendamento.

        Returns:
            DateTime do fim do agendamento
        """
        return self.scheduled_datetime + timedelta(minutes=self.duration_minutes)

    @property
    def formatted_date(self) -> str:
        """
        Retorna a data formatada (pt-BR).

        Returns:
            Data formatada (ex: "15/01/2024")
        """
        return self.scheduled_date.strftime("%d/%m/%Y")

    @property
    def formatted_time(self) -> str:
        """
        Retorna o horário formatado.

        Returns:
            Horário formatado (ex: "14:30")
        """
        return self.scheduled_time.strftime("%H:%M")

    @property
    def formatted_datetime(self) -> str:
        """
        Retorna data e hora formatadas.

        Returns:
            Data e hora formatadas (ex: "15/01/2024 às 14:30")
        """
        return f"{self.formatted_date} às {self.formatted_time}"

    @property
    def is_upcoming(self) -> bool:
        """
        Verifica se o agendamento é futuro.

        Returns:
            True se for futuro, False caso contrário
        """
        return self.scheduled_datetime > datetime.now()

    @property
    def is_past(self) -> bool:
        """
        Verifica se o agendamento já passou.

        Returns:
            True se passou, False caso contrário
        """
        return self.end_datetime < datetime.now()

    @property
    def is_today(self) -> bool:
        """
        Verifica se o agendamento é hoje.

        Returns:
            True se for hoje, False caso contrário
        """
        return self.scheduled_date == date.today()

    @property
    def is_active(self) -> bool:
        """
        Verifica se o agendamento está ativo (não cancelado/concluído).

        Returns:
            True se ativo, False caso contrário
        """
        return self.status in {AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED}

    @property
    def can_be_cancelled(self) -> bool:
        """
        Verifica se o agendamento pode ser cancelado.

        Returns:
            True se pode ser cancelado, False caso contrário
        """
        return (
            self.is_active
            and self.is_upcoming
            and self.status != AppointmentStatus.CANCELLED
        )

    def cancel(
        self,
        reason: str | None = None,
        cancelled_by: CancelledBy = CancelledBy.CUSTOMER
    ) -> None:
        """
        Cancela o agendamento.

        Args:
            reason: Motivo do cancelamento
            cancelled_by: Quem está cancelando
        """
        self.status = AppointmentStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_by = cancelled_by

    def confirm(self) -> None:
        """Confirma o agendamento."""
        self.status = AppointmentStatus.CONFIRMED

    def complete(self) -> None:
        """Marca o agendamento como concluído."""
        self.status = AppointmentStatus.COMPLETED

    def mark_no_show(self) -> None:
        """Marca o cliente como não comparecido."""
        self.status = AppointmentStatus.NO_SHOW

    def send_reminder(self) -> None:
        """Marca que o lembrete foi enviado."""
        self.reminder_sent = True
        self.reminder_sent_at = datetime.now(timezone.utc)

    def hours_until_appointment(self) -> float:
        """
        Calcula quantas horas faltam até o agendamento.

        Returns:
            Número de horas (pode ser negativo se já passou)
        """
        delta = self.scheduled_datetime - datetime.now()
        return delta.total_seconds() / 3600

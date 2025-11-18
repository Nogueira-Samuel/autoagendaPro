"""
Business Configuration Model

Configurações específicas de cada negócio (tenant).
Define horários de funcionamento, mensagens automáticas, regras de agendamento, etc.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class BusinessConfig(Base):
    """
    Modelo de Configuração de Negócio.

    Armazena todas as configurações personalizáveis de um tenant,
    incluindo horários de funcionamento, durações padrão, mensagens, etc.

    Attributes:
        id: Identificador único da configuração
        tenant_id: ID do tenant (relação 1:1)
        business_hours: JSON com horários de funcionamento por dia da semana
        default_appointment_duration: Duração padrão de agendamentos (minutos)
        buffer_time: Tempo de buffer entre agendamentos (minutos)
        max_advance_booking_days: Quantos dias no futuro permitir agendamentos
        auto_confirm_appointments: Se agendamentos são confirmados automaticamente
        send_reminders: Se deve enviar lembretes
        reminder_hours_before: Horas antes do agendamento para enviar lembrete
        cancellation_hours_before: Horas mínimas antes para cancelar
        welcome_message: Mensagem de boas-vindas para novos clientes
        confirmation_message_template: Template de mensagem de confirmação
        reminder_message_template: Template de mensagem de lembrete
        cancellation_message_template: Template de mensagem de cancelamento
        created_at: Data de criação
        updated_at: Data da última atualização
    """

    __tablename__ = "business_configs"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Tenant Relationship (1:1)
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="ID do tenant (relação 1:1)"
    )

    # Business Hours
    business_hours: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="""
        Horários de funcionamento por dia da semana.
        Formato: {
            "monday": {"open": "09:00", "close": "18:00", "is_open": true},
            "tuesday": {"open": "09:00", "close": "18:00", "is_open": true},
            ...
            "sunday": {"is_open": false}
        }
        """
    )

    # Appointment Settings
    default_appointment_duration: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Duração padrão de agendamentos em minutos"
    )

    buffer_time: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Tempo de buffer entre agendamentos em minutos"
    )

    max_advance_booking_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="Quantos dias no futuro permitir agendamentos"
    )

    auto_confirm_appointments: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Se agendamentos são confirmados automaticamente"
    )

    # Reminder Settings
    send_reminders: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Se deve enviar lembretes automáticos"
    )

    reminder_hours_before: Mapped[int] = mapped_column(
        Integer,
        default=24,
        nullable=False,
        comment="Horas antes do agendamento para enviar lembrete"
    )

    # Cancellation Settings
    cancellation_hours_before: Mapped[int] = mapped_column(
        Integer,
        default=24,
        nullable=False,
        comment="Horas mínimas antes do agendamento para permitir cancelamento"
    )

    # Message Templates
    welcome_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="Olá! Bem-vindo(a). Como posso ajudá-lo(a) hoje?",
        comment="Mensagem de boas-vindas para novos clientes"
    )

    confirmation_message_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="""
Olá {customer_name}!

Seu agendamento foi confirmado:
📅 Data: {date}
🕐 Horário: {time}
💼 Serviço: {service}

Nos vemos em breve!
        """.strip(),
        comment="""
        Template de confirmação. Variáveis disponíveis:
        {customer_name}, {date}, {time}, {service}, {duration}
        """
    )

    reminder_message_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="""
Olá {customer_name}!

Este é um lembrete do seu agendamento:
📅 Data: {date}
🕐 Horário: {time}
💼 Serviço: {service}

Até lá!
        """.strip(),
        comment="""
        Template de lembrete. Variáveis disponíveis:
        {customer_name}, {date}, {time}, {service}, {duration}
        """
    )

    cancellation_message_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="""
Olá {customer_name},

Seu agendamento foi cancelado:
📅 Data: {date}
🕐 Horário: {time}

Se precisar reagendar, é só me chamar!
        """.strip(),
        comment="""
        Template de cancelamento. Variáveis disponíveis:
        {customer_name}, {date}, {time}, {service}, {reason}
        """
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
        back_populates="business_config",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return f"<BusinessConfig(id={self.id}, tenant_id={self.tenant_id})>"

    def get_business_hours_for_day(self, day: str) -> dict | None:
        """
        Retorna os horários de funcionamento para um dia específico.

        Args:
            day: Nome do dia em inglês (monday, tuesday, etc.)

        Returns:
            Dict com horários ou None se não configurado
        """
        if not self.business_hours:
            return None
        return self.business_hours.get(day.lower())

    def is_open_on_day(self, day: str) -> bool:
        """
        Verifica se o negócio abre em um determinado dia.

        Args:
            day: Nome do dia em inglês (monday, tuesday, etc.)

        Returns:
            True se abre, False caso contrário
        """
        hours = self.get_business_hours_for_day(day)
        if not hours:
            return False
        return hours.get("is_open", False)

    def format_message(
        self,
        template: str,
        customer_name: str | None = None,
        date: str | None = None,
        time: str | None = None,
        service: str | None = None,
        duration: str | None = None,
        reason: str | None = None,
    ) -> str:
        """
        Formata uma mensagem substituindo as variáveis.

        Args:
            template: Template da mensagem
            customer_name: Nome do cliente
            date: Data do agendamento
            time: Horário do agendamento
            service: Nome do serviço
            duration: Duração do serviço
            reason: Razão do cancelamento

        Returns:
            Mensagem formatada
        """
        return template.format(
            customer_name=customer_name or "",
            date=date or "",
            time=time or "",
            service=service or "",
            duration=duration or "",
            reason=reason or "",
        )

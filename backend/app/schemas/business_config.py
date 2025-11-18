"""
Business Config Schemas

Pydantic schemas for BusinessConfig model validation.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class BusinessHours(BaseModel):
    """
    Schema para horários de funcionamento de um dia.

    Attributes:
        open: Horário de abertura (formato HH:MM)
        close: Horário de fechamento (formato HH:MM)
        is_open: Se o negócio abre neste dia
    """

    open: str = Field(
        default="09:00",
        description="Horário de abertura (formato HH:MM)",
        pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
        examples=["09:00", "08:30"],
    )
    close: str = Field(
        default="18:00",
        description="Horário de fechamento (formato HH:MM)",
        pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$",
        examples=["18:00", "17:30"],
    )
    is_open: bool = Field(
        default=True,
        description="Se o negócio abre neste dia",
    )

    @field_validator("open", "close")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """
        Valida o formato do horário (HH:MM).

        Args:
            v: Horário a validar

        Returns:
            Horário validado

        Raises:
            ValueError: Se o formato não for válido
        """
        if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError(
                f"Horário inválido: {v}. Formato esperado: HH:MM (ex: 09:00)"
            )
        return v

    def model_post_init(self, __context) -> None:
        """
        Validação após inicialização do modelo.

        Verifica se horário de abertura é menor que fechamento.

        Raises:
            ValueError: Se open >= close
        """
        if self.is_open and self.open >= self.close:
            raise ValueError(
                f"Horário de abertura ({self.open}) deve ser menor que "
                f"horário de fechamento ({self.close})"
            )


class BusinessConfigBase(BaseModel):
    """
    Base BusinessConfig schema with common fields.

    Attributes:
        business_hours: Horários de funcionamento por dia da semana
        default_appointment_duration: Duração padrão de agendamentos (minutos)
        buffer_time: Tempo de buffer entre agendamentos (minutos)
        max_advance_booking_days: Quantos dias no futuro permitir agendamentos
        auto_confirm_appointments: Se agendamentos são confirmados automaticamente
        send_reminders: Se deve enviar lembretes
        reminder_hours_before: Horas antes para enviar lembrete
        cancellation_hours_before: Horas mínimas antes para cancelar
    """

    business_hours: dict[str, BusinessHours] | None = Field(
        default=None,
        description="Horários de funcionamento por dia da semana",
        examples=[
            {
                "monday": {"open": "09:00", "close": "18:00", "is_open": True},
                "tuesday": {"open": "09:00", "close": "18:00", "is_open": True},
                "sunday": {"is_open": False},
            }
        ],
    )
    default_appointment_duration: int = Field(
        default=60,
        ge=15,
        le=480,
        description="Duração padrão de agendamentos em minutos (15-480)",
        examples=[60],
    )
    buffer_time: int = Field(
        default=0,
        ge=0,
        le=60,
        description="Tempo de buffer entre agendamentos em minutos (0-60)",
        examples=[15],
    )
    max_advance_booking_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Quantos dias no futuro permitir agendamentos (1-365)",
        examples=[30],
    )
    auto_confirm_appointments: bool = Field(
        default=False,
        description="Se agendamentos são confirmados automaticamente",
    )
    send_reminders: bool = Field(
        default=True,
        description="Se deve enviar lembretes automáticos",
    )
    reminder_hours_before: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Horas antes do agendamento para enviar lembrete (1-168)",
        examples=[24],
    )
    cancellation_hours_before: int = Field(
        default=2,
        ge=0,
        le=72,
        description="Horas mínimas antes do agendamento para permitir cancelamento (0-72)",
        examples=[24],
    )

    @field_validator("business_hours")
    @classmethod
    def validate_business_hours(cls, v: dict[str, BusinessHours] | None) -> dict[str, BusinessHours] | None:
        """
        Valida os dias da semana nos horários de funcionamento.

        Args:
            v: Dicionário de horários

        Returns:
            Horários validados

        Raises:
            ValueError: Se houver dias inválidos
        """
        if v is None:
            return v

        valid_days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }

        invalid_days = set(v.keys()) - valid_days
        if invalid_days:
            raise ValueError(
                f"Dias inválidos: {invalid_days}. "
                f"Dias válidos: {valid_days}"
            )

        return v


class BusinessConfigCreate(BusinessConfigBase):
    """
    Schema para criação de BusinessConfig.

    Inclui tenant_id e templates de mensagens.
    """

    tenant_id: int = Field(
        ...,
        description="ID do tenant",
        examples=[1],
    )
    welcome_message: str | None = Field(
        default=None,
        description="Mensagem de boas-vindas para novos clientes",
        examples=["Olá! Bem-vindo(a). Como posso ajudá-lo(a) hoje?"],
    )
    confirmation_message_template: str | None = Field(
        default=None,
        description="Template de mensagem de confirmação (variáveis: {customer_name}, {date}, {time}, {service})",
        examples=[
            "Olá {customer_name}! Seu agendamento foi confirmado para {date} às {time}. Serviço: {service}"
        ],
    )
    reminder_message_template: str | None = Field(
        default=None,
        description="Template de mensagem de lembrete",
        examples=[
            "Lembrete: você tem agendamento amanhã às {time}. Serviço: {service}"
        ],
    )
    cancellation_message_template: str | None = Field(
        default=None,
        description="Template de mensagem de cancelamento",
        examples=["Seu agendamento para {date} às {time} foi cancelado."],
    )


class BusinessConfigUpdate(BaseModel):
    """
    Schema para atualização de BusinessConfig.

    Todos os campos são opcionais.
    """

    business_hours: dict[str, BusinessHours] | None = Field(
        default=None,
        description="Horários de funcionamento",
    )
    default_appointment_duration: int | None = Field(
        default=None,
        ge=15,
        le=480,
        description="Duração padrão em minutos",
    )
    buffer_time: int | None = Field(
        default=None,
        ge=0,
        le=60,
        description="Tempo de buffer em minutos",
    )
    max_advance_booking_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Dias no futuro para agendamentos",
    )
    auto_confirm_appointments: bool | None = Field(
        default=None,
        description="Auto-confirmar agendamentos",
    )
    send_reminders: bool | None = Field(
        default=None,
        description="Enviar lembretes",
    )
    reminder_hours_before: int | None = Field(
        default=None,
        ge=1,
        le=168,
        description="Horas antes para lembrete",
    )
    cancellation_hours_before: int | None = Field(
        default=None,
        ge=0,
        le=72,
        description="Horas mínimas para cancelar",
    )
    welcome_message: str | None = Field(
        default=None,
        description="Mensagem de boas-vindas",
    )
    confirmation_message_template: str | None = Field(
        default=None,
        description="Template de confirmação",
    )
    reminder_message_template: str | None = Field(
        default=None,
        description="Template de lembrete",
    )
    cancellation_message_template: str | None = Field(
        default=None,
        description="Template de cancelamento",
    )


class BusinessConfigResponse(BusinessConfigBase):
    """
    Schema para resposta de BusinessConfig.

    Inclui todos os campos do banco de dados.
    """

    id: int = Field(..., description="ID único da configuração")
    tenant_id: int = Field(..., description="ID do tenant")
    welcome_message: str | None = Field(
        default=None,
        description="Mensagem de boas-vindas",
    )
    confirmation_message_template: str | None = Field(
        default=None,
        description="Template de confirmação",
    )
    reminder_message_template: str | None = Field(
        default=None,
        description="Template de lembrete",
    )
    cancellation_message_template: str | None = Field(
        default=None,
        description="Template de cancelamento",
    )
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)

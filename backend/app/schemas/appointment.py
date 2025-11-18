"""
Appointment Schemas

Pydantic schemas for Appointment model validation.
"""

from datetime import datetime, date, time

from pydantic import BaseModel, Field, ConfigDict, field_validator


class AppointmentBase(BaseModel):
    """
    Base Appointment schema with common fields.

    Attributes:
        scheduled_date: Data do agendamento
        scheduled_time: Horário do agendamento
        duration_minutes: Duração em minutos
        notes: Observações
    """

    scheduled_date: date = Field(
        ...,
        description="Data do agendamento",
        examples=["2024-01-15"],
    )
    scheduled_time: time = Field(
        ...,
        description="Horário do agendamento",
        examples=["14:30:00", "09:00:00"],
    )
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=480,
        description="Duração do agendamento em minutos (15-480)",
        examples=[60],
    )
    notes: str | None = Field(
        default=None,
        description="Observações sobre o agendamento",
        examples=["Cliente solicitou sala com janela"],
    )

    @field_validator("scheduled_date")
    @classmethod
    def validate_date_not_past(cls, v: date) -> date:
        """
        Valida que a data não está no passado.

        Args:
            v: Data a validar

        Returns:
            Data validada

        Raises:
            ValueError: Se a data for anterior a hoje
        """
        from datetime import date as date_class

        today = date_class.today()
        if v < today:
            raise ValueError(
                f"Data do agendamento ({v}) não pode ser no passado. "
                f"Data mínima: {today}"
            )

        return v


class AppointmentCreate(AppointmentBase):
    """
    Schema para criação de Appointment.

    Inclui IDs de tenant, customer e service.
    """

    tenant_id: int = Field(
        ...,
        description="ID do tenant",
        examples=[1],
    )
    customer_id: int = Field(
        ...,
        description="ID do cliente",
        examples=[10],
    )
    service_id: int = Field(
        ...,
        description="ID do serviço",
        examples=[5],
    )


class AppointmentUpdate(BaseModel):
    """
    Schema para atualização de Appointment.

    Todos os campos são opcionais.
    """

    scheduled_date: date | None = Field(
        default=None,
        description="Data do agendamento",
    )
    scheduled_time: time | None = Field(
        default=None,
        description="Horário do agendamento",
    )
    duration_minutes: int | None = Field(
        default=None,
        ge=15,
        le=480,
        description="Duração em minutos",
    )
    notes: str | None = Field(
        default=None,
        description="Observações",
    )
    status: str | None = Field(
        default=None,
        description="Status do agendamento",
        pattern="^(pending|confirmed|cancelled|completed|no_show)$",
        examples=["confirmed"],
    )

    @field_validator("scheduled_date")
    @classmethod
    def validate_date_not_past(cls, v: date | None) -> date | None:
        """Valida que a data não está no passado se fornecida."""
        if v is None:
            return v

        from datetime import date as date_class

        today = date_class.today()
        if v < today:
            raise ValueError(
                f"Data do agendamento ({v}) não pode ser no passado. "
                f"Data mínima: {today}"
            )

        return v


class AppointmentCancel(BaseModel):
    """
    Schema para cancelamento de Appointment.

    Attributes:
        cancellation_reason: Motivo do cancelamento
        cancelled_by: Quem cancelou
    """

    cancellation_reason: str = Field(
        ...,
        min_length=10,
        description="Motivo do cancelamento (mínimo 10 caracteres)",
        examples=[
            "Cliente solicitou reagendamento",
            "Médico precisou viajar de emergência",
        ],
    )
    cancelled_by: str = Field(
        ...,
        description="Quem cancelou o agendamento",
        pattern="^(customer|business|system)$",
        examples=["customer", "business"],
    )


class AppointmentResponse(AppointmentBase):
    """
    Schema para resposta de Appointment.

    Inclui todos os campos do banco de dados.
    """

    id: int = Field(..., description="ID único do agendamento")
    tenant_id: int = Field(..., description="ID do tenant")
    customer_id: int = Field(..., description="ID do cliente")
    service_id: int = Field(..., description="ID do serviço")
    status: str = Field(
        ...,
        description="Status do agendamento",
        examples=["pending", "confirmed"],
    )
    google_calendar_event_id: str | None = Field(
        default=None,
        description="ID do evento no Google Calendar",
    )
    cancellation_reason: str | None = Field(
        default=None,
        description="Motivo do cancelamento",
    )
    cancelled_by: str | None = Field(
        default=None,
        description="Quem cancelou",
    )
    reminder_sent: bool = Field(
        ...,
        description="Se lembrete foi enviado",
    )
    reminder_sent_at: datetime | None = Field(
        default=None,
        description="Quando o lembrete foi enviado",
    )
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)


class AppointmentWithRelations(AppointmentResponse):
    """
    Schema para resposta de Appointment com relações incluídas.

    Opcional: Inclui dados de customer e service aninhados.
    """

    # Você pode adicionar campos aninhados aqui se quiser retornar
    # dados completos de customer e service junto com o appointment
    # Por exemplo:
    # customer: CustomerResponse
    # service: ServiceResponse

    # Por enquanto, deixaremos apenas com IDs
    # As relações podem ser carregadas separadamente pelos IDs
    pass

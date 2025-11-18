"""
Tenant Schemas

Pydantic schemas for Tenant model validation.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TenantBase(BaseModel):
    """
    Base Tenant schema with common fields.

    Attributes:
        name: Nome do negócio
        slug: Identificador URL-friendly único
        is_active: Status do tenant
        plan: Plano de assinatura
        timezone: Timezone do negócio
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Nome do negócio",
        examples=["Clínica Dr. Silva"],
    )
    slug: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Identificador único URL-friendly (lowercase, sem espaços)",
        examples=["clinica-dr-silva"],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se o tenant está ativo",
    )
    plan: str = Field(
        ...,
        description="Plano de assinatura",
        pattern="^(free|basic|premium|enterprise)$",
        examples=["basic"],
    )
    timezone: str = Field(
        default="America/Sao_Paulo",
        description="Timezone do negócio",
        examples=["America/Sao_Paulo", "America/New_York"],
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """
        Valida e normaliza o slug.

        O slug deve conter apenas letras minúsculas, números e hífens.

        Args:
            v: Valor do slug

        Returns:
            Slug normalizado (lowercase)

        Raises:
            ValueError: Se o slug não for válido
        """
        # Converte para lowercase
        v = v.lower()

        # Valida formato: apenas letras, números e hífens
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Slug deve conter apenas letras minúsculas, números e hífens"
            )

        # Não pode começar ou terminar com hífen
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Slug não pode começar ou terminar com hífen")

        # Não pode ter hífens consecutivos
        if "--" in v:
            raise ValueError("Slug não pode ter hífens consecutivos")

        return v


class TenantCreate(TenantBase):
    """
    Schema para criação de Tenant.

    Inclui campos opcionais para configuração de integrações.
    """

    google_calendar_credentials: dict | None = Field(
        default=None,
        description="Credenciais JSON da Service Account do Google Calendar",
    )
    google_calendar_id: str | None = Field(
        default=None,
        max_length=255,
        description="ID do calendário do Google Calendar",
        examples=["primary", "example@group.calendar.google.com"],
    )
    evolution_instance_name: str | None = Field(
        default=None,
        max_length=100,
        description="Nome da instância no Evolution API",
        examples=["autoagenda-clinica"],
    )
    evolution_api_key: str | None = Field(
        default=None,
        description="API key da instância Evolution (será criptografada)",
    )


class TenantUpdate(BaseModel):
    """
    Schema para atualização de Tenant.

    Todos os campos são opcionais.
    """

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Nome do negócio",
    )
    is_active: bool | None = Field(
        default=None,
        description="Status do tenant",
    )
    plan: str | None = Field(
        default=None,
        pattern="^(free|basic|premium|enterprise)$",
        description="Plano de assinatura",
    )
    google_calendar_credentials: dict | None = Field(
        default=None,
        description="Credenciais JSON da Service Account do Google Calendar",
    )
    google_calendar_id: str | None = Field(
        default=None,
        max_length=255,
        description="ID do calendário do Google Calendar",
    )
    evolution_instance_name: str | None = Field(
        default=None,
        max_length=100,
        description="Nome da instância no Evolution API",
    )
    evolution_api_key: str | None = Field(
        default=None,
        description="API key da instância Evolution",
    )
    timezone: str | None = Field(
        default=None,
        description="Timezone do negócio",
    )


class TenantResponse(TenantBase):
    """
    Schema para resposta de Tenant.

    Inclui campos do banco de dados, excluindo dados sensíveis.
    Não inclui: google_calendar_credentials, evolution_api_key
    """

    id: int = Field(..., description="ID único do tenant")
    google_calendar_id: str | None = Field(
        default=None,
        description="ID do calendário configurado (se houver)",
    )
    evolution_instance_name: str | None = Field(
        default=None,
        description="Nome da instância Evolution configurada (se houver)",
    )
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)

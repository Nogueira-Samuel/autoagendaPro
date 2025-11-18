"""
Service Schemas

Pydantic schemas for Service model validation.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ServiceBase(BaseModel):
    """
    Base Service schema with common fields.

    Attributes:
        name: Nome do serviço
        description: Descrição detalhada
        duration_minutes: Duração em minutos
        price: Preço do serviço
        is_active: Status do serviço
        color: Cor hexadecimal para calendário
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Nome do serviço",
        examples=["Consulta Médica", "Corte de Cabelo"],
    )
    description: str | None = Field(
        default=None,
        description="Descrição detalhada do serviço",
        examples=["Consulta médica geral com duração de 1 hora"],
    )
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=480,
        description="Duração do serviço em minutos (15-480)",
        examples=[60],
    )
    price: float | None = Field(
        default=None,
        ge=0,
        description="Preço do serviço (opcional)",
        examples=[150.00],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se o serviço está disponível para agendamento",
    )
    color: str = Field(
        default="#3B82F6",
        description="Cor hexadecimal para exibição no calendário",
        pattern="^#[0-9A-Fa-f]{6}$",
        examples=["#3B82F6", "#10B981", "#F59E0B"],
    )

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """
        Valida o formato da cor hexadecimal.

        A cor deve estar no formato #RRGGBB (6 dígitos hexadecimais).

        Args:
            v: Cor a validar

        Returns:
            Cor validada (uppercase)

        Raises:
            ValueError: Se o formato não for válido
        """
        # Remove espaços
        v = v.strip()

        # Verifica se começa com #
        if not v.startswith("#"):
            raise ValueError("Cor deve começar com # (ex: #3B82F6)")

        # Verifica formato hexadecimal
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError(
                "Cor inválida. Formato esperado: #RRGGBB com 6 dígitos "
                "hexadecimais (ex: #3B82F6, #FF5733)"
            )

        # Retorna em uppercase para consistência
        return v.upper()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float | None) -> float | None:
        """
        Valida o preço se fornecido.

        Args:
            v: Preço a validar

        Returns:
            Preço validado (2 casas decimais)

        Raises:
            ValueError: Se o preço for negativo
        """
        if v is None:
            return v

        if v < 0:
            raise ValueError("Preço não pode ser negativo")

        # Arredonda para 2 casas decimais
        return round(v, 2)


class ServiceCreate(ServiceBase):
    """
    Schema para criação de Service.

    Inclui tenant_id.
    """

    tenant_id: int = Field(
        ...,
        description="ID do tenant que oferece o serviço",
        examples=[1],
    )


class ServiceUpdate(BaseModel):
    """
    Schema para atualização de Service.

    Todos os campos são opcionais.
    """

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Nome do serviço",
    )
    description: str | None = Field(
        default=None,
        description="Descrição do serviço",
    )
    duration_minutes: int | None = Field(
        default=None,
        ge=15,
        le=480,
        description="Duração em minutos",
    )
    price: float | None = Field(
        default=None,
        ge=0,
        description="Preço do serviço",
    )
    is_active: bool | None = Field(
        default=None,
        description="Status do serviço",
    )
    color: str | None = Field(
        default=None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Cor hexadecimal",
    )

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """
        Valida o formato da cor se fornecida.

        Args:
            v: Cor a validar

        Returns:
            Cor validada ou None

        Raises:
            ValueError: Se o formato não for válido
        """
        if v is None:
            return v

        v = v.strip()

        if not v.startswith("#"):
            raise ValueError("Cor deve começar com #")

        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Formato de cor inválido. Use #RRGGBB")

        return v.upper()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float | None) -> float | None:
        """Valida o preço se fornecido."""
        if v is None:
            return v

        if v < 0:
            raise ValueError("Preço não pode ser negativo")

        return round(v, 2)


class ServiceResponse(ServiceBase):
    """
    Schema para resposta de Service.

    Inclui campos do banco de dados.
    """

    id: int = Field(..., description="ID único do serviço")
    tenant_id: int = Field(..., description="ID do tenant")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)

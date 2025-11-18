"""
Customer Schemas

Pydantic schemas for Customer model validation.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr


class CustomerBase(BaseModel):
    """
    Base Customer schema with common fields.

    Attributes:
        phone: Número de telefone WhatsApp (formato brasileiro)
        name: Nome do cliente
        email: Email do cliente
        notes: Notas internas
        is_blocked: Status de bloqueio
        preferred_language: Idioma preferido
    """

    phone: str = Field(
        ...,
        description="Número de telefone WhatsApp no formato brasileiro (5521999999999)",
        pattern="^55[1-9]{2}9?[0-9]{8}$",
        examples=["5521987654321", "5511999887766"],
    )
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Nome do cliente",
        examples=["Maria Silva"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="Email do cliente (opcional)",
        examples=["maria@email.com"],
    )
    notes: str | None = Field(
        default=None,
        description="Notas internas sobre o cliente",
        examples=["Cliente preferencial, sempre pontual"],
    )
    is_blocked: bool = Field(
        default=False,
        description="Indica se o cliente está bloqueado",
    )
    preferred_language: str = Field(
        default="pt-BR",
        description="Idioma preferido do cliente",
        pattern="^[a-z]{2}-[A-Z]{2}$",
        examples=["pt-BR", "en-US"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """
        Valida e normaliza o número de telefone brasileiro.

        Formato esperado: 55 + DDD (2 dígitos) + número (8 ou 9 dígitos)
        Exemplos válidos:
        - 5521999999999 (celular com 9 dígitos)
        - 5521988888888 (celular)
        - 5521333333333 (fixo com 8 dígitos)

        Args:
            v: Número de telefone

        Returns:
            Telefone normalizado (apenas dígitos)

        Raises:
            ValueError: Se o formato não for válido
        """
        # Remove caracteres não numéricos
        phone_digits = re.sub(r"\D", "", v)

        # Valida formato brasileiro: 55 + DDD (2 dígitos) + número (8 ou 9 dígitos)
        # DDD válido: 11-99 (não pode começar com 0)
        # Celular: 9 dígitos (começa com 9)
        # Fixo: 8 dígitos
        pattern = r"^55[1-9]{2}9?[0-9]{8}$"

        if not re.match(pattern, phone_digits):
            raise ValueError(
                f"Número de telefone inválido: {v}. "
                "Formato esperado: 55 + DDD + número (ex: 5521987654321 para celular, "
                "5521333333333 para fixo)"
            )

        # Valida DDD (deve estar entre 11 e 99)
        ddd = int(phone_digits[2:4])
        if ddd < 11 or ddd > 99:
            raise ValueError(
                f"DDD inválido: {ddd}. DDD deve estar entre 11 e 99"
            )

        return phone_digits

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """
        Valida o nome se fornecido.

        Args:
            v: Nome a validar

        Returns:
            Nome validado (com espaços normalizados)

        Raises:
            ValueError: Se o nome for inválido
        """
        if v is None:
            return v

        # Remove espaços extras
        v = " ".join(v.split())

        # Verifica tamanho mínimo
        if len(v) < 3:
            raise ValueError("Nome deve ter pelo menos 3 caracteres")

        return v


class CustomerCreate(CustomerBase):
    """
    Schema para criação de Customer.

    Inclui tenant_id.
    """

    tenant_id: int = Field(
        ...,
        description="ID do tenant ao qual o cliente pertence",
        examples=[1],
    )


class CustomerUpdate(BaseModel):
    """
    Schema para atualização de Customer.

    Todos os campos são opcionais.
    Não permite atualizar phone ou tenant_id.
    """

    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Nome do cliente",
    )
    email: EmailStr | None = Field(
        default=None,
        description="Email do cliente",
    )
    notes: str | None = Field(
        default=None,
        description="Notas internas",
    )
    is_blocked: bool | None = Field(
        default=None,
        description="Status de bloqueio",
    )
    preferred_language: str | None = Field(
        default=None,
        pattern="^[a-z]{2}-[A-Z]{2}$",
        description="Idioma preferido",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Valida o nome se fornecido."""
        if v is None:
            return v

        v = " ".join(v.split())

        if len(v) < 3:
            raise ValueError("Nome deve ter pelo menos 3 caracteres")

        return v


class CustomerResponse(CustomerBase):
    """
    Schema para resposta de Customer.

    Inclui campos do banco de dados.
    """

    id: int = Field(..., description="ID único do cliente")
    tenant_id: int = Field(..., description="ID do tenant")
    last_interaction: datetime | None = Field(
        default=None,
        description="Data/hora da última interação via WhatsApp",
    )
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)

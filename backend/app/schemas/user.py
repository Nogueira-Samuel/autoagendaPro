"""
User Schemas

Pydantic schemas for User model validation.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr


class UserBase(BaseModel):
    """
    Base User schema with common fields.

    Attributes:
        email: Email do usuário
        full_name: Nome completo
        role: Papel no sistema
        is_active: Status do usuário
    """

    email: EmailStr = Field(
        ...,
        description="Email do usuário",
        examples=["admin@clinica.com"],
    )
    full_name: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Nome completo do usuário",
        examples=["João Silva"],
    )
    role: str = Field(
        ...,
        description="Papel do usuário no sistema",
        pattern="^(super_admin|admin|operator|viewer)$",
        examples=["admin"],
    )
    is_active: bool = Field(
        default=True,
        description="Indica se o usuário está ativo",
    )


class UserCreate(UserBase):
    """
    Schema para criação de User.

    Inclui tenant_id (nullable para super_admin) e password.
    """

    tenant_id: int | None = Field(
        default=None,
        description="ID do tenant (null para super_admin)",
        examples=[1],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Senha do usuário (mínimo 8 caracteres, deve conter letra e número)",
        examples=["Senha123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Valida a força da senha.

        A senha deve ter:
        - Mínimo 8 caracteres
        - Pelo menos uma letra
        - Pelo menos um número

        Args:
            v: Senha a validar

        Returns:
            Senha validada

        Raises:
            ValueError: Se a senha não atender aos requisitos
        """
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")

        # Verifica se tem pelo menos uma letra
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Senha deve conter pelo menos uma letra")

        # Verifica se tem pelo menos um número
        if not re.search(r"\d", v):
            raise ValueError("Senha deve conter pelo menos um número")

        return v


class UserLogin(BaseModel):
    """
    Schema para login de usuário.

    Attributes:
        email: Email do usuário
        password: Senha do usuário
        tenant_id: ID do tenant
    """

    email: EmailStr = Field(
        ...,
        description="Email do usuário",
        examples=["admin@clinica.com"],
    )
    password: str = Field(
        ...,
        description="Senha do usuário",
        examples=["Senha123!"],
    )
    tenant_id: int = Field(
        ...,
        description="ID do tenant",
        examples=[1],
    )


class UserUpdate(BaseModel):
    """
    Schema para atualização de User.

    Todos os campos são opcionais.
    """

    email: EmailStr | None = Field(
        default=None,
        description="Email do usuário",
    )
    full_name: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="Nome completo",
    )
    role: str | None = Field(
        default=None,
        pattern="^(super_admin|admin|operator|viewer)$",
        description="Papel do usuário",
    )
    is_active: bool | None = Field(
        default=None,
        description="Status do usuário",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        description="Nova senha",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """
        Valida a força da senha se fornecida.

        Args:
            v: Senha a validar

        Returns:
            Senha validada ou None

        Raises:
            ValueError: Se a senha não atender aos requisitos
        """
        if v is None:
            return v

        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")

        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Senha deve conter pelo menos uma letra")

        if not re.search(r"\d", v):
            raise ValueError("Senha deve conter pelo menos um número")

        return v


class UserResponse(UserBase):
    """
    Schema para resposta de User.

    Inclui campos do banco de dados, excluindo password_hash.
    """

    id: int = Field(..., description="ID único do usuário")
    tenant_id: int | None = Field(
        default=None,
        description="ID do tenant (null para super_admin)",
    )
    last_login: datetime | None = Field(
        default=None,
        description="Data/hora do último login",
    )
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data da última atualização")

    model_config = ConfigDict(from_attributes=True)

"""
Customer Model

Modelo de clientes finais (end customers).
Pessoas que agendam consultas/serviços via WhatsApp.
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Index,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.appointment import Appointment
    from app.models.conversation import Conversation


class Customer(Base):
    """
    Modelo de Cliente Final.

    Representa os clientes que interagem via WhatsApp para agendar serviços.
    Cada cliente pertence a um tenant específico.

    Attributes:
        id: Identificador único do cliente
        tenant_id: ID do tenant ao qual o cliente pertence
        phone: Número de telefone WhatsApp (formato: 5521999999999)
        name: Nome do cliente (extraído da conversa)
        email: Email do cliente (opcional)
        notes: Notas internas sobre o cliente
        is_blocked: Indica se o cliente está bloqueado
        preferred_language: Idioma preferido do cliente
        created_at: Data de criação
        updated_at: Data da última atualização
        last_interaction: Data/hora da última interação
    """

    __tablename__ = "customers"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Tenant Relationship
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID do tenant ao qual o cliente pertence"
    )

    # Contact Information
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Número de telefone WhatsApp (formato: 5521999999999)"
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nome do cliente (pode ser extraído da conversa)"
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email do cliente (opcional)"
    )

    # Internal Information
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Notas internas sobre o cliente"
    )

    # Status
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Indica se o cliente está bloqueado"
    )

    # Preferences
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="pt-BR",
        nullable=False,
        comment="Idioma preferido do cliente"
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

    last_interaction: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Data/hora da última interação via WhatsApp"
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="customers",
        lazy="selectin"
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes and Constraints
    __table_args__ = (
        # Telefone único por tenant
        UniqueConstraint(
            "tenant_id", "phone",
            name="uq_customer_tenant_phone"
        ),
        Index("idx_customer_tenant_id", "tenant_id"),
        Index("idx_customer_tenant_phone", "tenant_id", "phone"),
        Index("idx_customer_is_blocked", "tenant_id", "is_blocked"),
        Index("idx_customer_last_interaction", "last_interaction"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return (
            f"<Customer(id={self.id}, name='{self.name}', "
            f"phone='{self.phone}', tenant_id={self.tenant_id})>"
        )

    @validates("phone")
    def validate_phone(self, key: str, phone: str) -> str:
        """
        Valida e normaliza o número de telefone.

        Args:
            key: Nome do campo
            phone: Número de telefone a validar

        Returns:
            Número de telefone normalizado

        Raises:
            ValueError: Se o número não for válido
        """
        # Remove caracteres não numéricos
        phone_digits = re.sub(r"\D", "", phone)

        # Valida formato brasileiro (55 + DDD + número)
        # Exemplos válidos: 5521999999999, 5511988888888
        if not re.match(r"^55\d{10,11}$", phone_digits):
            raise ValueError(
                f"Número de telefone inválido: {phone}. "
                "Formato esperado: 55 + DDD + número (ex: 5521999999999)"
            )

        return phone_digits

    @validates("email")
    def validate_email(self, key: str, email: str | None) -> str | None:
        """
        Valida o formato do email.

        Args:
            key: Nome do campo
            email: Email a validar

        Returns:
            Email validado ou None

        Raises:
            ValueError: Se o email não for válido
        """
        if email is None or email.strip() == "":
            return None

        email = email.strip().lower()

        # Validação básica de email
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError(f"Email inválido: {email}")

        return email

    @property
    def formatted_phone(self) -> str:
        """
        Retorna o telefone formatado para exibição.

        Returns:
            Telefone formatado (ex: +55 (21) 99999-9999)
        """
        if not self.phone:
            return ""

        # Remove o código do país
        phone_without_country = self.phone[2:]

        # Extrai DDD e número
        ddd = phone_without_country[:2]
        number = phone_without_country[2:]

        # Formata de acordo com o tamanho
        if len(number) == 9:  # Celular
            return f"+55 ({ddd}) {number[:5]}-{number[5:]}"
        elif len(number) == 8:  # Fixo
            return f"+55 ({ddd}) {number[:4]}-{number[4:]}"
        else:
            return f"+{self.phone}"

    @property
    def display_name(self) -> str:
        """
        Retorna o nome para exibição.

        Returns:
            Nome do cliente ou telefone formatado se nome não disponível
        """
        return self.name or self.formatted_phone

    @property
    def is_active(self) -> bool:
        """
        Verifica se o cliente está ativo (não bloqueado).

        Returns:
            True se ativo, False se bloqueado
        """
        return not self.is_blocked

    def update_last_interaction(self) -> None:
        """Atualiza a data/hora da última interação para agora."""
        self.last_interaction = datetime.utcnow()


# Event listener para normalizar telefone antes de inserir/atualizar
@event.listens_for(Customer, "before_insert")
@event.listens_for(Customer, "before_update")
def normalize_phone_before_save(mapper, connection, target):
    """
    Normaliza o telefone antes de salvar no banco.

    Args:
        mapper: SQLAlchemy mapper
        connection: Conexão do banco
        target: Instância do modelo Customer
    """
    if target.phone:
        # Remove todos os caracteres não numéricos
        target.phone = re.sub(r"\D", "", target.phone)

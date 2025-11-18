"""
User Model

Modelo de usuários do sistema (administradores, operadores, visualizadores).
Usuários são pessoas que gerenciam o sistema, não os clientes finais.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Index, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class UserRole(str, enum.Enum):
    """Papéis (roles) de usuário no sistema."""
    SUPER_ADMIN = "super_admin"  # Acesso total a todos os tenants
    ADMIN = "admin"              # Administrador do tenant
    OPERATOR = "operator"        # Operador - pode gerenciar agendamentos
    VIEWER = "viewer"            # Apenas visualização


class User(Base):
    """
    Modelo de Usuário do Sistema.

    Representa usuários que têm acesso ao sistema de gerenciamento
    (não os clientes finais que agendam via WhatsApp).

    Attributes:
        id: Identificador único do usuário
        tenant_id: ID do tenant (null para super_admin)
        email: Email do usuário (único por tenant)
        password_hash: Hash bcrypt da senha
        full_name: Nome completo do usuário
        role: Papel do usuário no sistema
        is_active: Indica se o usuário está ativo
        last_login: Data/hora do último login
        created_at: Data de criação
        updated_at: Data da última atualização
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Tenant Relationship
    tenant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # Null para super_admin
        index=True,
        comment="ID do tenant (null para super_admin)"
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Email do usuário"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash bcrypt da senha"
    )

    # User Information
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome completo do usuário"
    )

    # Role and Status
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.VIEWER,
        nullable=False,
        comment="Papel do usuário no sistema"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Indica se o usuário está ativo"
    )

    # Activity Tracking
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Data/hora do último login"
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
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant",
        back_populates="users",
        lazy="selectin"
    )

    # Indexes and Constraints
    __table_args__ = (
        # Email único por tenant (permite mesmo email em tenants diferentes)
        UniqueConstraint(
            "email", "tenant_id",
            name="uq_user_email_tenant"
        ),
        Index("idx_user_tenant_id", "tenant_id"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_email_tenant", "email", "tenant_id"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}', tenant_id={self.tenant_id})>"

    @property
    def is_super_admin(self) -> bool:
        """Verifica se o usuário é super administrador."""
        return self.role == UserRole.SUPER_ADMIN and self.tenant_id is None

    @property
    def is_admin(self) -> bool:
        """Verifica se o usuário é administrador (de tenant ou super)."""
        return self.role in {UserRole.SUPER_ADMIN, UserRole.ADMIN}

    @property
    def can_manage_appointments(self) -> bool:
        """Verifica se o usuário pode gerenciar agendamentos."""
        return self.role in {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.OPERATOR}

    @property
    def can_manage_settings(self) -> bool:
        """Verifica se o usuário pode gerenciar configurações."""
        return self.role in {UserRole.SUPER_ADMIN, UserRole.ADMIN}

    def has_access_to_tenant(self, tenant_id: int) -> bool:
        """
        Verifica se o usuário tem acesso a um tenant específico.

        Args:
            tenant_id: ID do tenant a verificar

        Returns:
            True se o usuário tem acesso, False caso contrário
        """
        if self.is_super_admin:
            return True
        return self.tenant_id == tenant_id

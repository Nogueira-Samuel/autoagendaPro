"""
Conversation Model

Modelo de conversas via WhatsApp.
Armazena histórico completo de mensagens para contexto da IA.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON

from app.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.customer import Customer


class MessageDirection(str, enum.Enum):
    """Direção da mensagem."""
    INBOUND = "inbound"      # Mensagem recebida (do cliente)
    OUTBOUND = "outbound"    # Mensagem enviada (do negócio)


class MessageType(str, enum.Enum):
    """Tipo de mensagem."""
    TEXT = "text"            # Mensagem de texto
    IMAGE = "image"          # Imagem
    AUDIO = "audio"          # Áudio/voz
    DOCUMENT = "document"    # Documento/arquivo
    LOCATION = "location"    # Localização
    VIDEO = "video"          # Vídeo
    STICKER = "sticker"      # Sticker
    CONTACT = "contact"      # Contato


class Conversation(Base):
    """
    Modelo de Conversa.

    Armazena o histórico completo de mensagens trocadas via WhatsApp.
    Usado para fornecer contexto para a IA Claude e análise de conversas.

    Attributes:
        id: Identificador único da mensagem
        tenant_id: ID do tenant
        customer_id: ID do cliente
        message_id: ID único da mensagem no WhatsApp
        direction: Direção da mensagem (recebida ou enviada)
        message_type: Tipo da mensagem (texto, imagem, etc)
        content: Conteúdo textual da mensagem
        media_url: URL do arquivo de mídia (se aplicável)
        context: Contexto da conversa para a IA (JSON)
        intent: Intenção detectada pela IA
        sentiment: Sentimento detectado (positivo, neutro, negativo)
        processed: Indica se a mensagem foi processada
        created_at: Data/hora de criação (recebimento/envio)
    """

    __tablename__ = "conversations"

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

    # Message Identification
    message_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="ID único da mensagem no WhatsApp"
    )

    # Message Properties
    direction: Mapped[MessageDirection] = mapped_column(
        SQLEnum(MessageDirection, name="message_direction"),
        nullable=False,
        comment="Direção da mensagem (recebida ou enviada)"
    )

    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType, name="message_type"),
        default=MessageType.TEXT,
        nullable=False,
        comment="Tipo da mensagem"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Conteúdo textual da mensagem"
    )

    media_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="URL do arquivo de mídia (imagem, áudio, documento, etc)"
    )

    # AI Context and Analysis
    context: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="""
        Contexto da conversa para a IA Claude.
        Pode incluir: histórico resumido, variáveis de estado,
        preferências, informações extraídas, etc.
        """
    )

    intent: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="""
        Intenção detectada pela IA.
        Exemplos: schedule, cancel, reschedule, inquiry, greeting, etc.
        """
    )

    sentiment: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Sentimento detectado: positive, neutral, negative"
    )

    # Processing Status
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Indica se a mensagem foi processada pela IA"
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Data/hora de criação (recebimento ou envio)"
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="conversations",
        lazy="selectin"
    )

    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="conversations",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_conversation_tenant_id", "tenant_id"),
        Index("idx_conversation_customer_id", "customer_id"),
        Index("idx_conversation_message_id", "message_id"),
        Index("idx_conversation_tenant_customer_created", "tenant_id", "customer_id", "created_at"),
        Index("idx_conversation_tenant_created", "tenant_id", "created_at"),
        Index("idx_conversation_processed", "processed"),
        Index("idx_conversation_intent", "intent"),
    )

    def __repr__(self) -> str:
        """Representação em string do modelo."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<Conversation(id={self.id}, customer_id={self.customer_id}, "
            f"direction='{self.direction.value}', content='{content_preview}')>"
        )

    @property
    def is_inbound(self) -> bool:
        """Verifica se a mensagem foi recebida (do cliente)."""
        return self.direction == MessageDirection.INBOUND

    @property
    def is_outbound(self) -> bool:
        """Verifica se a mensagem foi enviada (do negócio)."""
        return self.direction == MessageDirection.OUTBOUND

    @property
    def has_media(self) -> bool:
        """Verifica se a mensagem contém mídia."""
        return self.media_url is not None

    @property
    def is_text_only(self) -> bool:
        """Verifica se é apenas mensagem de texto."""
        return self.message_type == MessageType.TEXT and not self.has_media

    @property
    def formatted_timestamp(self) -> str:
        """
        Retorna timestamp formatado.

        Returns:
            String formatada (ex: "15/01/2024 14:30")
        """
        return self.created_at.strftime("%d/%m/%Y %H:%M")

    def mark_as_processed(self) -> None:
        """Marca a mensagem como processada."""
        self.processed = True

    def set_intent(self, intent: str) -> None:
        """
        Define a intenção detectada.

        Args:
            intent: Intenção detectada (ex: "schedule", "cancel")
        """
        self.intent = intent.lower()

    def set_sentiment(self, sentiment: str) -> None:
        """
        Define o sentimento detectado.

        Args:
            sentiment: Sentimento (positive, neutral, negative)
        """
        allowed_sentiments = {"positive", "neutral", "negative"}
        if sentiment.lower() not in allowed_sentiments:
            raise ValueError(f"Sentiment must be one of {allowed_sentiments}")
        self.sentiment = sentiment.lower()

    def update_context(self, new_context: dict) -> None:
        """
        Atualiza o contexto da conversa.

        Args:
            new_context: Novo contexto (será merged com o existente)
        """
        if self.context is None:
            self.context = {}

        # Merge do novo contexto com o existente
        self.context.update(new_context)

    def get_context_value(self, key: str, default=None):
        """
        Obtém um valor do contexto.

        Args:
            key: Chave do contexto
            default: Valor padrão se a chave não existir

        Returns:
            Valor do contexto ou default
        """
        if self.context is None:
            return default
        return self.context.get(key, default)

    @classmethod
    def get_conversation_history(
        cls,
        customer_id: int,
        tenant_id: int,
        limit: int = 10
    ):
        """
        Obtém o histórico de conversas de um cliente.

        Args:
            customer_id: ID do cliente
            tenant_id: ID do tenant
            limit: Número máximo de mensagens

        Returns:
            Query para buscar histórico
        """
        # Nota: Esta é uma classe method que retorna uma query
        # A execução real deve ser feita no serviço/router
        from sqlalchemy import select

        return (
            select(cls)
            .where(cls.customer_id == customer_id)
            .where(cls.tenant_id == tenant_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )

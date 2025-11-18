"""
Conversation Schemas

Pydantic schemas for Conversation model validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ConversationBase(BaseModel):
    """
    Base Conversation schema with common fields.

    Attributes:
        message_id: ID único da mensagem no WhatsApp
        direction: Direção da mensagem (inbound/outbound)
        message_type: Tipo da mensagem
        content: Conteúdo textual
        media_url: URL do arquivo de mídia
    """

    message_id: str = Field(
        ...,
        description="ID único da mensagem no WhatsApp",
        examples=["3EB0C67D4F9A2B5E8D1C"],
    )
    direction: str = Field(
        ...,
        description="Direção da mensagem",
        pattern="^(inbound|outbound)$",
        examples=["inbound", "outbound"],
    )
    message_type: str = Field(
        ...,
        description="Tipo da mensagem",
        pattern="^(text|image|audio|document|location|video|sticker|contact)$",
        examples=["text", "image"],
    )
    content: str | None = Field(
        default=None,
        description="Conteúdo textual da mensagem",
        examples=["Olá, gostaria de agendar uma consulta"],
    )
    media_url: str | None = Field(
        default=None,
        description="URL do arquivo de mídia (imagem, áudio, documento, etc)",
        examples=["https://example.com/media/image123.jpg"],
    )


class ConversationCreate(ConversationBase):
    """
    Schema para criação de Conversation.

    Inclui tenant_id, customer_id e campos de análise de IA.
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
    context: dict | None = Field(
        default=None,
        description="Contexto da conversa para a IA Claude",
        examples=[
            {
                "conversation_state": "scheduling",
                "mentioned_service": "consulta",
                "preferred_date": "2024-01-15",
            }
        ],
    )
    intent: str | None = Field(
        default=None,
        description="Intenção detectada pela IA",
        examples=["schedule", "cancel", "reschedule", "inquiry", "greeting"],
    )
    sentiment: str | None = Field(
        default=None,
        description="Sentimento detectado",
        pattern="^(positive|neutral|negative)$",
        examples=["positive", "neutral"],
    )


class ConversationResponse(ConversationBase):
    """
    Schema para resposta de Conversation.

    Inclui todos os campos do banco de dados.
    """

    id: int = Field(..., description="ID único da mensagem")
    tenant_id: int = Field(..., description="ID do tenant")
    customer_id: int = Field(..., description="ID do cliente")
    context: dict | None = Field(
        default=None,
        description="Contexto da conversa",
    )
    intent: str | None = Field(
        default=None,
        description="Intenção detectada",
    )
    sentiment: str | None = Field(
        default=None,
        description="Sentimento detectado",
    )
    processed: bool = Field(
        ...,
        description="Indica se a mensagem foi processada pela IA",
    )
    created_at: datetime = Field(
        ...,
        description="Data/hora de criação (recebimento ou envio)",
    )

    model_config = ConfigDict(from_attributes=True)

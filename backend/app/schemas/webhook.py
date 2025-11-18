"""
Webhook Schemas

Pydantic schemas for incoming WhatsApp webhooks (Evolution API).
"""

from pydantic import BaseModel, Field, ConfigDict


class WhatsAppWebhookMessage(BaseModel):
    """
    Schema para mensagem do webhook WhatsApp.

    Representa uma mensagem recebida via Evolution API.

    Attributes:
        key: Informações da chave da mensagem (id, remoteJid, fromMe, etc)
        message: Conteúdo da mensagem
        messageType: Tipo da mensagem
        messageTimestamp: Timestamp Unix da mensagem
        pushName: Nome do remetente
        status: Status da mensagem
    """

    key: dict = Field(
        ...,
        description="Chave da mensagem contendo id, remoteJid, fromMe, etc",
        examples=[
            {
                "id": "3EB0C67D4F9A2B5E8D1C",
                "remoteJid": "5521987654321@s.whatsapp.net",
                "fromMe": False,
            }
        ],
    )
    message: dict | None = Field(
        default=None,
        description="Conteúdo da mensagem",
        examples=[
            {
                "conversation": "Olá, gostaria de agendar uma consulta",
            }
        ],
    )
    messageType: str = Field(
        ...,
        description="Tipo da mensagem",
        examples=["conversation", "extendedTextMessage", "imageMessage"],
    )
    messageTimestamp: int = Field(
        ...,
        description="Timestamp Unix da mensagem",
        examples=[1704067200],
    )
    pushName: str | None = Field(
        default=None,
        description="Nome do remetente conforme aparece no WhatsApp",
        examples=["Maria Silva"],
    )
    status: str | None = Field(
        default=None,
        description="Status da mensagem",
        examples=["PENDING", "SERVER_ACK", "DELIVERY_ACK", "READ"],
    )

    model_config = ConfigDict(from_attributes=False)


class WhatsAppWebhookData(BaseModel):
    """
    Schema para dados do webhook WhatsApp.

    Envolve a mensagem com metadados da instância.

    Attributes:
        instance: Nome da instância Evolution API
        data: Dados da mensagem
        destination: Destino da mensagem
        date_time: Data/hora do evento
        server_url: URL do servidor Evolution
        apikey: API key da instância
    """

    instance: str = Field(
        ...,
        description="Nome da instância Evolution API",
        examples=["autoagenda-clinica"],
    )
    data: WhatsAppWebhookMessage = Field(
        ...,
        description="Dados da mensagem recebida",
    )
    destination: str | None = Field(
        default=None,
        description="Destino da mensagem",
        examples=["5521999999999@s.whatsapp.net"],
    )
    date_time: str | None = Field(
        default=None,
        description="Data/hora do evento",
        examples=["2024-01-01T12:00:00.000Z"],
    )
    server_url: str | None = Field(
        default=None,
        description="URL do servidor Evolution API",
        examples=["https://evolution-api.example.com"],
    )
    apikey: str | None = Field(
        default=None,
        description="API key da instância (para validação)",
    )

    model_config = ConfigDict(from_attributes=False)


class WhatsAppWebhookEvent(BaseModel):
    """
    Schema para evento de webhook WhatsApp.

    Representa o evento completo recebido do Evolution API.

    Attributes:
        event: Tipo do evento
        instance: Nome da instância
        data: Dados do webhook
    """

    event: str = Field(
        ...,
        description="Tipo do evento",
        examples=[
            "messages.upsert",
            "messages.update",
            "connection.update",
            "qrcode.updated",
        ],
    )
    instance: str = Field(
        ...,
        description="Nome da instância Evolution API",
        examples=["autoagenda-clinica"],
    )
    data: WhatsAppWebhookData = Field(
        ...,
        description="Dados do webhook",
    )

    model_config = ConfigDict(from_attributes=False)


class WhatsAppSendMessageRequest(BaseModel):
    """
    Schema para envio de mensagem via Evolution API.

    Usado quando o sistema precisa enviar mensagens para clientes.

    Attributes:
        number: Número de telefone do destinatário
        text: Texto da mensagem
        delay: Delay antes de enviar (opcional, em ms)
    """

    number: str = Field(
        ...,
        description="Número de telefone do destinatário (formato: 5521999999999)",
        examples=["5521987654321"],
    )
    text: str = Field(
        ...,
        description="Texto da mensagem a enviar",
        examples=["Olá! Seu agendamento foi confirmado para amanhã às 14h."],
    )
    delay: int | None = Field(
        default=None,
        ge=0,
        le=10000,
        description="Delay antes de enviar a mensagem (em milissegundos)",
        examples=[1000],
    )

    model_config = ConfigDict(from_attributes=False)


class WhatsAppSendMessageResponse(BaseModel):
    """
    Schema para resposta de envio de mensagem.

    Retornado pelo Evolution API após enviar mensagem.

    Attributes:
        key: Chave da mensagem enviada
        message: Conteúdo enviado
        messageTimestamp: Timestamp do envio
        status: Status do envio
    """

    key: dict = Field(
        ...,
        description="Chave da mensagem enviada",
    )
    message: dict = Field(
        ...,
        description="Conteúdo da mensagem enviada",
    )
    messageTimestamp: int = Field(
        ...,
        description="Timestamp Unix do envio",
    )
    status: str = Field(
        ...,
        description="Status do envio",
        examples=["PENDING", "SERVER_ACK"],
    )

    model_config = ConfigDict(from_attributes=False)

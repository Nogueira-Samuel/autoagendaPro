"""
WhatsApp Service Base Classes

Abstract base classes for WhatsApp integration.
Permite múltiplos provedores (Evolution API, WhatsApp Business API, etc).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MediaType(str, Enum):
    """Tipos de mídia suportados pelo WhatsApp."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class WhatsAppError(Exception):
    """Erro base para operações WhatsApp."""

    pass


class WhatsAppConnectionError(WhatsAppError):
    """Erro de conexão com API WhatsApp."""

    pass


class WhatsAppRateLimitError(WhatsAppError):
    """Erro de rate limit da API WhatsApp."""

    pass


class WhatsAppAuthenticationError(WhatsAppError):
    """Erro de autenticação com API WhatsApp."""

    pass


class WhatsAppMessageError(WhatsAppError):
    """Erro ao enviar mensagem WhatsApp."""

    pass


@dataclass
class WhatsAppMessage:
    """
    Mensagem WhatsApp a ser enviada.

    Attributes:
        phone: Número do destinatário (formato: 5521999999999)
        content: Conteúdo da mensagem (texto)
        media_url: URL da mídia (opcional)
        media_type: Tipo da mídia (opcional)
        caption: Legenda para mídia (opcional)
        quoted_message_id: ID da mensagem a ser citada (opcional)
        metadata: Metadados adicionais (opcional)
    """

    phone: str
    content: str
    media_url: str | None = None
    media_type: MediaType | None = None
    caption: str | None = None
    quoted_message_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validações após inicialização."""
        # Valida formato do telefone
        if not self.phone:
            raise ValueError("Número de telefone é obrigatório")

        # Remove caracteres não numéricos
        self.phone = "".join(filter(str.isdigit, self.phone))

        # Valida formato brasileiro
        if not self.phone.startswith("55"):
            raise ValueError("Número deve começar com código do Brasil (55)")

        if len(self.phone) < 12 or len(self.phone) > 13:
            raise ValueError(
                f"Número inválido: {self.phone}. "
                "Formato esperado: 55 + DDD + número (ex: 5521999999999)"
            )

        # Valida mídia
        if self.media_url and not self.media_type:
            raise ValueError("media_type é obrigatório quando media_url está presente")

        if self.media_type and not self.media_url:
            raise ValueError("media_url é obrigatório quando media_type está presente")

    @property
    def is_media_message(self) -> bool:
        """Verifica se é mensagem de mídia."""
        return self.media_url is not None and self.media_type is not None

    @property
    def formatted_phone(self) -> str:
        """Retorna telefone formatado para exibição."""
        if len(self.phone) == 13:  # Celular com 9 dígitos
            return f"+{self.phone[:2]} ({self.phone[2:4]}) {self.phone[4:9]}-{self.phone[9:]}"
        else:  # Fixo com 8 dígitos
            return f"+{self.phone[:2]} ({self.phone[2:4]}) {self.phone[4:8]}-{self.phone[8:]}"


@dataclass
class WhatsAppResponse:
    """
    Resposta de operação WhatsApp.

    Attributes:
        success: Indica se operação foi bem-sucedida
        message_id: ID da mensagem enviada (se sucesso)
        error: Mensagem de erro (se falha)
        status_code: Código HTTP da resposta
        provider_response: Resposta completa do provedor
        timestamp: Timestamp da operação
    """

    success: bool
    message_id: str | None = None
    error: str | None = None
    status_code: int | None = None
    provider_response: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validações após inicialização."""
        if self.success and not self.message_id:
            raise ValueError("message_id é obrigatório quando success=True")

        if not self.success and not self.error:
            raise ValueError("error é obrigatório quando success=False")


@dataclass
class ConnectionStatus:
    """
    Status da conexão WhatsApp.

    Attributes:
        connected: Indica se está conectado
        instance_name: Nome da instância
        phone_number: Número conectado (se conectado)
        qr_code: Código QR para conexão (se desconectado)
        status: Status detalhado (open, connecting, close, etc)
        battery_level: Nível de bateria do dispositivo
        platform: Plataforma (android, ios, etc)
    """

    connected: bool
    instance_name: str
    phone_number: str | None = None
    qr_code: str | None = None
    status: str = "unknown"
    battery_level: int | None = None
    platform: str | None = None
    last_checked: datetime = field(default_factory=datetime.utcnow)


class WhatsAppServiceBase(ABC):
    """
    Classe abstrata base para serviços WhatsApp.

    Implementações concretas devem herdar desta classe e implementar
    todos os métodos abstratos.

    Provedores suportados:
    - Evolution API
    - WhatsApp Business API (futuro)
    - Twilio WhatsApp (futuro)
    """

    def __init__(
        self,
        tenant_id: int,
        instance_name: str,
        api_url: str | None = None,
        api_key: str | None = None,
    ):
        """
        Inicializa serviço WhatsApp.

        Args:
            tenant_id: ID do tenant (multi-tenant)
            instance_name: Nome da instância WhatsApp
            api_url: URL base da API (opcional)
            api_key: Chave de autenticação (opcional)
        """
        self.tenant_id = tenant_id
        self.instance_name = instance_name
        self.api_url = api_url
        self.api_key = api_key

    @abstractmethod
    async def send_text(
        self,
        phone: str,
        message: str,
        quoted_message_id: str | None = None,
    ) -> WhatsAppResponse:
        """
        Envia mensagem de texto.

        Args:
            phone: Número do destinatário
            message: Conteúdo da mensagem
            quoted_message_id: ID da mensagem a citar (opcional)

        Returns:
            WhatsAppResponse com resultado

        Raises:
            WhatsAppMessageError: Se falha no envio
        """
        pass

    @abstractmethod
    async def send_media(
        self,
        phone: str,
        media_url: str,
        media_type: MediaType,
        caption: str | None = None,
    ) -> WhatsAppResponse:
        """
        Envia mensagem com mídia.

        Args:
            phone: Número do destinatário
            media_url: URL da mídia
            media_type: Tipo da mídia
            caption: Legenda (opcional)

        Returns:
            WhatsAppResponse com resultado

        Raises:
            WhatsAppMessageError: Se falha no envio
        """
        pass

    @abstractmethod
    async def check_connection(self) -> ConnectionStatus:
        """
        Verifica status da conexão WhatsApp.

        Returns:
            ConnectionStatus com informações da conexão

        Raises:
            WhatsAppConnectionError: Se falha ao verificar
        """
        pass

    @abstractmethod
    async def send_typing(self, phone: str, duration_seconds: int = 3) -> bool:
        """
        Envia indicador de digitação.

        Args:
            phone: Número do destinatário
            duration_seconds: Duração em segundos

        Returns:
            True se sucesso, False caso contrário
        """
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """
        Marca mensagem como lida.

        Args:
            message_id: ID da mensagem

        Returns:
            True se sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retorna nome do provedor.

        Returns:
            Nome do provedor (ex: "Evolution API", "WhatsApp Business API")
        """
        pass

    def _validate_phone(self, phone: str) -> str:
        """
        Valida e formata número de telefone.

        Args:
            phone: Número a validar

        Returns:
            Número formatado

        Raises:
            ValueError: Se número inválido
        """
        # Remove caracteres não numéricos
        phone_clean = "".join(filter(str.isdigit, phone))

        # Adiciona código do Brasil se não tiver
        if not phone_clean.startswith("55"):
            # Assume que é número brasileiro sem código
            phone_clean = f"55{phone_clean}"

        # Valida tamanho
        if len(phone_clean) < 12 or len(phone_clean) > 13:
            raise ValueError(
                f"Número de telefone inválido: {phone}. "
                "Formato esperado: 55 + DDD + número"
            )

        return phone_clean

    def __repr__(self) -> str:
        """Representação string do serviço."""
        return (
            f"{self.__class__.__name__}("
            f"tenant_id={self.tenant_id}, "
            f"instance={self.instance_name}, "
            f"provider={self.get_provider_name()})"
        )

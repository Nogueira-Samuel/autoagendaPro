"""
Evolution API WhatsApp Service

Implementação concreta do serviço WhatsApp usando Evolution API.
Documentação: https://doc.evolution-api.com
"""

import asyncio
import logging
from typing import Any, TYPE_CHECKING

import httpx

from app.services.whatsapp_base import (
    WhatsAppServiceBase,
    WhatsAppMessage,
    WhatsAppResponse,
    ConnectionStatus,
    MediaType,
    WhatsAppError,
    WhatsAppConnectionError,
    WhatsAppRateLimitError,
    WhatsAppAuthenticationError,
    WhatsAppMessageError,
)

if TYPE_CHECKING:
    from app.models import Tenant

logger = logging.getLogger(__name__)


class EvolutionAPIService(WhatsAppServiceBase):
    """
    Serviço WhatsApp usando Evolution API.

    Evolution API é uma API REST para integração com WhatsApp
    que suporta múltiplas instâncias e recursos avançados.

    Features:
    - Envio de texto e mídia
    - Indicador de digitação
    - Marcar como lido
    - Gerenciamento de conexão
    - QR Code para pareamento
    - Status da instância

    Endpoints principais:
    - POST /message/sendText/{instance}
    - POST /message/sendMedia/{instance}
    - GET /instance/connectionState/{instance}
    - POST /chat/markMessageRead/{instance}
    """

    def __init__(
        self,
        tenant_id: int,
        instance_name: str,
        api_url: str,
        api_key: str,
        timeout: int = 30,
    ):
        """
        Inicializa serviço Evolution API.

        Args:
            tenant_id: ID do tenant
            instance_name: Nome da instância
            api_url: URL base da API (ex: https://api.evolution.com)
            api_key: Chave de autenticação
            timeout: Timeout para requisições em segundos
        """
        super().__init__(tenant_id, instance_name, api_url, api_key)
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

        logger.info(
            f"Evolution API service initialized: "
            f"tenant_id={tenant_id}, instance={instance_name}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Obtém cliente HTTP (lazy initialization).

        Returns:
            Cliente httpx configurado
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=self.timeout,
                headers=self._build_headers(),
            )
        return self._client

    async def close(self):
        """Fecha cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _build_headers(self) -> dict[str, str]:
        """
        Constrói headers para requisições.

        Returns:
            Dicionário de headers
        """
        return {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para Evolution API.

        Evolution API espera: 5521999999999@s.whatsapp.net

        Args:
            phone: Número do telefone

        Returns:
            Número formatado
        """
        # Valida e limpa
        phone_clean = self._validate_phone(phone)

        # Formato Evolution API
        return f"{phone_clean}@s.whatsapp.net"

    async def _handle_api_error(self, response: httpx.Response) -> None:
        """
        Processa erros da API.

        Args:
            response: Resposta HTTP

        Raises:
            WhatsAppAuthenticationError: Se erro 401
            WhatsAppConnectionError: Se erro 404
            WhatsAppRateLimitError: Se erro 429
            WhatsAppMessageError: Para outros erros
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get("message", response.text)
        except Exception:
            error_message = response.text

        # Log do erro
        logger.error(
            f"Evolution API error: status={status_code}, "
            f"instance={self.instance_name}, error={error_message}"
        )

        # Mapeia códigos de erro
        if status_code == 401:
            raise WhatsAppAuthenticationError(
                f"Autenticação falhou: {error_message}. Verifique API key."
            )
        elif status_code == 404:
            raise WhatsAppConnectionError(
                f"Instância não encontrada: {self.instance_name}. "
                f"Verifique se a instância existe."
            )
        elif status_code == 409:
            raise WhatsAppConnectionError(
                f"Conflito de estado: {error_message}. "
                f"A instância pode não estar conectada."
            )
        elif status_code == 429:
            raise WhatsAppRateLimitError(
                f"Rate limit atingido: {error_message}. Tente novamente em alguns segundos."
            )
        elif status_code >= 500:
            raise WhatsAppConnectionError(
                f"Erro do servidor Evolution API: {error_message}"
            )
        else:
            raise WhatsAppMessageError(
                f"Erro ao enviar mensagem: {error_message} (status={status_code})"
            )

    async def send_text(
        self,
        phone: str,
        message: str,
        quoted_message_id: str | None = None,
    ) -> WhatsAppResponse:
        """
        Envia mensagem de texto.

        API Endpoint: POST /message/sendText/{instance}

        Args:
            phone: Número do destinatário
            message: Conteúdo da mensagem
            quoted_message_id: ID da mensagem a citar (opcional)

        Returns:
            WhatsAppResponse com resultado
        """
        try:
            client = await self._get_client()
            phone_formatted = self._format_phone(phone)

            # Monta payload
            payload = {
                "number": phone_formatted,
                "text": message,
            }

            # Adiciona citação se fornecida
            if quoted_message_id:
                payload["quoted"] = {"key": {"id": quoted_message_id}}

            # Faz requisição
            response = await client.post(
                f"/message/sendText/{self.instance_name}",
                json=payload,
            )

            # Verifica erro
            if response.status_code != 200 and response.status_code != 201:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()

            logger.info(
                f"Text message sent: instance={self.instance_name}, "
                f"phone={phone}, message_id={data.get('key', {}).get('id')}"
            )

            return WhatsAppResponse(
                success=True,
                message_id=data.get("key", {}).get("id"),
                status_code=response.status_code,
                provider_response=data,
            )

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to send text message: {e}")
            raise

    async def send_media(
        self,
        phone: str,
        media_url: str,
        media_type: MediaType,
        caption: str | None = None,
    ) -> WhatsAppResponse:
        """
        Envia mensagem com mídia.

        API Endpoint: POST /message/sendMedia/{instance}

        Args:
            phone: Número do destinatário
            media_url: URL da mídia
            media_type: Tipo da mídia
            caption: Legenda (opcional)

        Returns:
            WhatsAppResponse com resultado
        """
        try:
            client = await self._get_client()
            phone_formatted = self._format_phone(phone)

            # Monta payload
            payload = {
                "number": phone_formatted,
                "mediatype": media_type.value,
                "media": media_url,
            }

            # Adiciona caption se fornecida
            if caption:
                payload["caption"] = caption

            # Faz requisição
            response = await client.post(
                f"/message/sendMedia/{self.instance_name}",
                json=payload,
            )

            # Verifica erro
            if response.status_code != 200 and response.status_code != 201:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()

            logger.info(
                f"Media message sent: instance={self.instance_name}, "
                f"phone={phone}, type={media_type}, message_id={data.get('key', {}).get('id')}"
            )

            return WhatsAppResponse(
                success=True,
                message_id=data.get("key", {}).get("id"),
                status_code=response.status_code,
                provider_response=data,
            )

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to send media message: {e}")
            raise

    async def send_location(
        self,
        phone: str,
        latitude: float,
        longitude: float,
        name: str | None = None,
        address: str | None = None,
    ) -> WhatsAppResponse:
        """
        Envia localização.

        API Endpoint: POST /message/sendLocation/{instance}

        Args:
            phone: Número do destinatário
            latitude: Latitude
            longitude: Longitude
            name: Nome do local (opcional)
            address: Endereço (opcional)

        Returns:
            WhatsAppResponse com resultado
        """
        try:
            client = await self._get_client()
            phone_formatted = self._format_phone(phone)

            # Monta payload
            payload = {
                "number": phone_formatted,
                "latitude": latitude,
                "longitude": longitude,
            }

            if name:
                payload["name"] = name
            if address:
                payload["address"] = address

            # Faz requisição
            response = await client.post(
                f"/message/sendLocation/{self.instance_name}",
                json=payload,
            )

            # Verifica erro
            if response.status_code != 200 and response.status_code != 201:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()

            logger.info(
                f"Location sent: instance={self.instance_name}, "
                f"phone={phone}, message_id={data.get('key', {}).get('id')}"
            )

            return WhatsAppResponse(
                success=True,
                message_id=data.get("key", {}).get("id"),
                status_code=response.status_code,
                provider_response=data,
            )

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to send location: {e}")
            raise

    async def check_connection(self) -> ConnectionStatus:
        """
        Verifica status da conexão WhatsApp.

        API Endpoint: GET /instance/connectionState/{instance}

        Returns:
            ConnectionStatus com informações da conexão
        """
        try:
            client = await self._get_client()

            # Faz requisição
            response = await client.get(
                f"/instance/connectionState/{self.instance_name}"
            )

            # Verifica erro
            if response.status_code != 200:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()

            # Evolution API retorna: { "state": "open" } ou { "state": "close" }
            state = data.get("state", "unknown")
            is_connected = state == "open"

            logger.info(
                f"Connection checked: instance={self.instance_name}, "
                f"connected={is_connected}, state={state}"
            )

            return ConnectionStatus(
                connected=is_connected,
                instance_name=self.instance_name,
                status=state,
                phone_number=data.get("instance", {}).get("phoneNumber"),
            )

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to check connection: {e}")
            raise WhatsAppConnectionError(f"Erro ao verificar conexão: {e}")

    async def get_qr_code(self) -> str:
        """
        Obtém QR Code para pareamento.

        API Endpoint: GET /instance/qrcode/{instance}

        Returns:
            Base64 do QR Code

        Raises:
            WhatsAppConnectionError: Se já conectado ou erro
        """
        try:
            client = await self._get_client()

            # Faz requisição
            response = await client.get(f"/instance/qrcode/{self.instance_name}")

            # Verifica erro
            if response.status_code != 200:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()
            qr_code = data.get("qrcode", {}).get("base64")

            if not qr_code:
                raise WhatsAppConnectionError("QR Code não disponível")

            logger.info(f"QR Code obtained: instance={self.instance_name}")

            return qr_code

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to get QR code: {e}")
            raise WhatsAppConnectionError(f"Erro ao obter QR Code: {e}")

    async def get_instance_info(self) -> dict[str, Any]:
        """
        Obtém informações da instância.

        API Endpoint: GET /instance/fetchInstances/{instance}

        Returns:
            Dicionário com informações da instância
        """
        try:
            client = await self._get_client()

            # Faz requisição
            response = await client.get(
                f"/instance/fetchInstances/{self.instance_name}"
            )

            # Verifica erro
            if response.status_code != 200:
                await self._handle_api_error(response)

            # Parse resposta
            data = response.json()

            logger.info(f"Instance info fetched: instance={self.instance_name}")

            return data

        except (WhatsAppError, httpx.HTTPError) as e:
            logger.error(f"Failed to get instance info: {e}")
            raise WhatsAppConnectionError(f"Erro ao obter info da instância: {e}")

    async def send_typing(self, phone: str, duration_seconds: int = 3) -> bool:
        """
        Envia indicador de digitação.

        API Endpoint: POST /chat/sendPresence/{instance}

        Args:
            phone: Número do destinatário
            duration_seconds: Duração em segundos

        Returns:
            True se sucesso
        """
        try:
            client = await self._get_client()
            phone_formatted = self._format_phone(phone)

            # Monta payload
            payload = {
                "number": phone_formatted,
                "presence": "composing",  # composing = digitando
                "delay": duration_seconds * 1000,  # API espera milissegundos
            }

            # Faz requisição
            response = await client.post(
                f"/chat/sendPresence/{self.instance_name}",
                json=payload,
            )

            # Verifica erro
            if response.status_code != 200 and response.status_code != 201:
                logger.warning(f"Failed to send typing indicator: {response.text}")
                return False

            logger.debug(
                f"Typing indicator sent: instance={self.instance_name}, phone={phone}"
            )

            return True

        except Exception as e:
            logger.warning(f"Failed to send typing indicator: {e}")
            return False

    async def mark_as_read(self, message_id: str) -> bool:
        """
        Marca mensagem como lida.

        API Endpoint: POST /chat/markMessageRead/{instance}

        Args:
            message_id: ID da mensagem

        Returns:
            True se sucesso
        """
        try:
            client = await self._get_client()

            # Monta payload
            payload = {
                "readMessages": [{"id": message_id}],
            }

            # Faz requisição
            response = await client.post(
                f"/chat/markMessageRead/{self.instance_name}",
                json=payload,
            )

            # Verifica erro
            if response.status_code != 200 and response.status_code != 201:
                logger.warning(f"Failed to mark message as read: {response.text}")
                return False

            logger.debug(
                f"Message marked as read: instance={self.instance_name}, "
                f"message_id={message_id}"
            )

            return True

        except Exception as e:
            logger.warning(f"Failed to mark message as read: {e}")
            return False

    def get_provider_name(self) -> str:
        """
        Retorna nome do provedor.

        Returns:
            Nome do provedor
        """
        return "Evolution API"

    @staticmethod
    async def create_from_tenant(tenant: "Tenant") -> "EvolutionAPIService":
        """
        Cria serviço a partir do tenant.

        Factory method que extrai configurações do tenant e cria instância.

        Args:
            tenant: Instância do modelo Tenant

        Returns:
            EvolutionAPIService configurado

        Raises:
            ValueError: Se configurações ausentes

        Example:
            >>> tenant = await db.get(Tenant, tenant_id)
            >>> whatsapp_service = await EvolutionAPIService.create_from_tenant(tenant)
            >>> await whatsapp_service.send_text("5521999999999", "Olá!")
        """
        # Valida configurações obrigatórias
        if not tenant.evolution_instance_name:
            raise ValueError(
                f"Tenant {tenant.id} não possui evolution_instance_name configurado"
            )

        # Obtém configurações (valores padrão se não configurados)
        from app.config import get_settings

        settings = get_settings()

        api_url = getattr(tenant, "evolution_api_url", None) or settings.EVOLUTION_API_URL
        api_key = (
            getattr(tenant, "evolution_api_key", None) or settings.EVOLUTION_API_KEY
        )

        if not api_url:
            raise ValueError("EVOLUTION_API_URL não configurado")

        if not api_key:
            raise ValueError("EVOLUTION_API_KEY não configurado")

        logger.info(
            f"Creating Evolution API service from tenant: "
            f"tenant_id={tenant.id}, instance={tenant.evolution_instance_name}"
        )

        return EvolutionAPIService(
            tenant_id=tenant.id,
            instance_name=tenant.evolution_instance_name,
            api_url=api_url,
            api_key=api_key,
        )

    async def __aenter__(self):
        """Context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

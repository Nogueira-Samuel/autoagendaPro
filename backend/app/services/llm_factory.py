"""
LLM Factory

Factory pattern para criar instâncias de serviços LLM.
Suporta seleção de provedor, fallback automático e configuração por tenant.
"""

import enum
import logging
from typing import TYPE_CHECKING

from app.services.llm_base import LLMServiceBase
from app.services.openai_service import OpenAIService
from app.services.claude_service import ClaudeService

if TYPE_CHECKING:
    from app.models import Tenant

logger = logging.getLogger(__name__)


class LLMProvider(str, enum.Enum):
    """Provedores de LLM disponíveis."""

    OPENAI = "openai"
    CLAUDE = "claude"


class LLMFactory:
    """
    Factory para criar instâncias de serviços LLM.

    Fornece métodos convenientes para:
    - Criar serviço por nome do provedor
    - Criar serviço baseado em configuração do tenant
    - Criar com fallback automático
    """

    @staticmethod
    def create(
        provider: str | LLMProvider, model: str | None = None
    ) -> LLMServiceBase:
        """
        Cria uma instância de serviço LLM.

        Args:
            provider: Nome do provedor ('openai' ou 'claude')
            model: Modelo específico a usar (opcional)

        Returns:
            Instância do serviço LLM

        Raises:
            ValueError: Se o provedor não for suportado

        Examples:
            >>> llm = LLMFactory.create("openai")
            >>> llm = LLMFactory.create("claude", model="claude-3-sonnet")
            >>> llm = LLMFactory.create(LLMProvider.OPENAI)
        """
        # Converte string para enum se necessário
        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider.lower())
            except ValueError:
                raise ValueError(
                    f"Provider '{provider}' não suportado. "
                    f"Use: {[p.value for p in LLMProvider]}"
                )

        # Cria instância baseado no provedor
        if provider == LLMProvider.OPENAI:
            logger.info(f"Creating OpenAI service with model: {model or 'default'}")
            return OpenAIService(model=model)

        elif provider == LLMProvider.CLAUDE:
            logger.info(f"Creating Claude service with model: {model or 'default'}")
            return ClaudeService(model=model)

        else:
            raise ValueError(f"Unknown provider: {provider}")

    @staticmethod
    def create_from_tenant(tenant: "Tenant") -> LLMServiceBase:
        """
        Cria serviço LLM baseado na configuração do tenant.

        Verifica atributos do tenant:
        - llm_provider: provedor a usar (openai, claude)
        - llm_model: modelo específico (opcional)

        Se não configurado, usa OpenAI GPT-3.5 Turbo como padrão.

        Args:
            tenant: Instância do modelo Tenant

        Returns:
            Instância do serviço LLM configurado

        Examples:
            >>> tenant = await db.get(Tenant, tenant_id)
            >>> llm = LLMFactory.create_from_tenant(tenant)
        """
        # Obtém configuração do tenant (com valores padrão)
        provider = getattr(tenant, "llm_provider", "openai")
        model = getattr(tenant, "llm_model", None)

        logger.info(
            f"Creating LLM service for tenant {tenant.id}: "
            f"provider={provider}, model={model or 'default'}"
        )

        return LLMFactory.create(provider, model)

    @staticmethod
    async def create_with_fallback(
        primary_provider: str | LLMProvider,
        fallback_provider: str | LLMProvider = LLMProvider.OPENAI,
        test_message: str = "Olá",
    ) -> LLMServiceBase:
        """
        Cria serviço LLM com fallback automático.

        Tenta criar e testar o provedor primário.
        Se falhar, usa o provedor de fallback.

        Args:
            primary_provider: Provedor principal
            fallback_provider: Provedor de fallback (padrão: OpenAI)
            test_message: Mensagem para testar o serviço

        Returns:
            Instância do serviço LLM (primário ou fallback)

        Examples:
            >>> llm = await LLMFactory.create_with_fallback("claude", "openai")
        """
        # Tenta criar provedor primário
        try:
            service = LLMFactory.create(primary_provider)

            # Testa o serviço (opcional)
            # await service.detect_intent(test_message)

            logger.info(f"Using primary provider: {primary_provider}")
            return service

        except Exception as e:
            logger.warning(
                f"Primary provider {primary_provider} failed: {e}. "
                f"Using fallback: {fallback_provider}"
            )

            # Cria fallback
            return LLMFactory.create(fallback_provider)

    @staticmethod
    def get_available_providers() -> list[str]:
        """
        Retorna lista de provedores disponíveis.

        Returns:
            Lista de nomes de provedores
        """
        return [provider.value for provider in LLMProvider]

    @staticmethod
    def get_default_models() -> dict[str, str]:
        """
        Retorna mapeamento de provedores para modelos padrão.

        Returns:
            Dicionário {provider: default_model}
        """
        return {
            "openai": "gpt-3.5-turbo",
            "claude": "claude-3-5-sonnet-20241022",
        }

    @staticmethod
    def get_provider_info(provider: str | LLMProvider) -> dict:
        """
        Retorna informações sobre um provedor.

        Args:
            provider: Nome do provedor

        Returns:
            Dicionário com informações do provedor
        """
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        info = {
            LLMProvider.OPENAI: {
                "name": "OpenAI",
                "models": [
                    "gpt-4-turbo-preview",
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "gpt-3.5-turbo-16k",
                ],
                "default_model": "gpt-3.5-turbo",
                "strengths": [
                    "Rápido",
                    "Custo-benefício",
                    "Function calling",
                    "JSON mode",
                ],
                "pricing_tier": "low-medium",
            },
            LLMProvider.CLAUDE: {
                "name": "Anthropic Claude",
                "models": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus",
                    "claude-3-sonnet",
                ],
                "default_model": "claude-3-5-sonnet-20241022",
                "strengths": [
                    "Contexto longo",
                    "Seguimento de instruções",
                    "Português nativo",
                    "Raciocínio complexo",
                ],
                "pricing_tier": "medium-high",
            },
        }

        return info.get(provider, {})


class LLMServicePool:
    """
    Pool de instâncias de serviços LLM para reuso.

    Mantém instâncias criadas para evitar recriação constante.
    Útil para otimização de performance.
    """

    def __init__(self):
        """Inicializa o pool vazio."""
        self._pool: dict[str, LLMServiceBase] = {}

    def get_or_create(
        self, provider: str | LLMProvider, model: str | None = None
    ) -> LLMServiceBase:
        """
        Obtém instância do pool ou cria nova.

        Args:
            provider: Nome do provedor
            model: Modelo específico

        Returns:
            Instância do serviço LLM
        """
        # Cria chave única para o pool
        key = f"{provider}:{model or 'default'}"

        # Retorna do pool se existir
        if key in self._pool:
            logger.debug(f"Reusing LLM service from pool: {key}")
            return self._pool[key]

        # Cria nova instância
        logger.debug(f"Creating new LLM service: {key}")
        service = LLMFactory.create(provider, model)
        self._pool[key] = service

        return service

    def clear(self):
        """Limpa o pool de instâncias."""
        self._pool.clear()
        logger.info("LLM service pool cleared")

    def size(self) -> int:
        """Retorna o tamanho do pool."""
        return len(self._pool)


# Instância global do pool (singleton)
_llm_pool = LLMServicePool()


def get_llm_pool() -> LLMServicePool:
    """
    Obtém a instância global do pool de serviços LLM.

    Returns:
        Instância do pool
    """
    return _llm_pool

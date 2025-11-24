"""
OpenAI Service

Implementação do serviço LLM usando OpenAI GPT models.
Suporta GPT-4 Turbo e GPT-3.5 Turbo com fallback automático.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from app.config import settings
from app.services.llm_base import LLMServiceBase, LLMResponse, ConversationContext

logger = logging.getLogger(__name__)


class OpenAIService(LLMServiceBase):
    """
    Serviço de LLM usando OpenAI GPT.

    Suporta múltiplos modelos com fallback automático e retry logic.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Inicializa o serviço OpenAI.

        Args:
            api_key: API key da OpenAI (usa settings se None)
            model: Modelo a usar (usa settings se None)
            max_tokens: Máximo de tokens na resposta
            temperature: Temperature para geração (0-2)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or getattr(
            settings, "OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo"
        )
        self.max_tokens = max_tokens or getattr(settings, "OPENAI_MAX_TOKENS", 500)
        self.temperature = temperature or getattr(
            settings, "OPENAI_TEMPERATURE", 0.7
        )

        # Cliente assíncrono OpenAI
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Modelos de fallback
        self.fallback_models = ["gpt-3.5-turbo", "gpt-3.5-turbo-16k"]

        logger.info(f"OpenAI service initialized with model: {self.model}")

    async def chat(
        self, prompt: str, context: ConversationContext
    ) -> LLMResponse:
        """
        Processa uma mensagem e retorna resposta estruturada.

        Args:
            prompt: Mensagem do usuário
            context: Contexto da conversa

        Returns:
            LLMResponse com resposta, intent e entidades

        Raises:
            Exception: Se falhar após todas as tentativas de retry
        """
        # Constrói mensagens para API
        messages = self._build_messages(prompt, context)

        # Tenta com modelo principal
        try:
            response = await self._call_openai(messages)
            return response
        except RateLimitError as e:
            logger.warning(f"Rate limit hit on {self.model}, retrying...")
            # Retry com backoff
            return await self._retry_with_backoff(messages)
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            # Tenta fallback
            return await self._try_fallback(messages)

    async def detect_intent(self, message: str) -> str:
        """
        Detecta a intenção de uma mensagem usando function calling.

        Args:
            message: Mensagem do usuário

        Returns:
            Intent: schedule, cancel, reschedule, inquiry, greeting, other
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você detecta a intenção de mensagens sobre agendamentos.",
                    },
                    {"role": "user", "content": message},
                ],
                functions=[
                    {
                        "name": "detect_intent",
                        "description": "Detecta a intenção da mensagem do usuário",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intent": {
                                    "type": "string",
                                    "enum": [
                                        "schedule",
                                        "cancel",
                                        "reschedule",
                                        "inquiry",
                                        "greeting",
                                        "other",
                                    ],
                                    "description": "Intenção detectada",
                                }
                            },
                            "required": ["intent"],
                        },
                    }
                ],
                function_call={"name": "detect_intent"},
                temperature=0.3,
            )

            # Extrai intent do function call
            function_call = response.choices[0].message.function_call
            if function_call:
                args = json.loads(function_call.arguments)
                return args.get("intent", "other")

        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            # Fallback para detecção baseada em keywords
            return self._parse_intent_from_response(message)

        return "other"

    async def extract_entities(self, message: str, intent: str) -> dict:
        """
        Extrai entidades de uma mensagem usando function calling.

        Args:
            message: Mensagem do usuário
            intent: Intenção detectada

        Returns:
            Dicionário com entidades (service, date, time, customer_name)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Extraia informações de agendamento. Intent: {intent}",
                    },
                    {"role": "user", "content": message},
                ],
                functions=[
                    {
                        "name": "extract_entities",
                        "description": "Extrai entidades da mensagem",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "service": {
                                    "type": "string",
                                    "description": "Nome do serviço mencionado",
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Data mencionada (YYYY-MM-DD)",
                                },
                                "time": {
                                    "type": "string",
                                    "description": "Horário mencionado (HH:MM)",
                                },
                                "customer_name": {
                                    "type": "string",
                                    "description": "Nome do cliente",
                                },
                            },
                        },
                    }
                ],
                function_call={"name": "extract_entities"},
                temperature=0.1,
            )

            # Extrai entidades do function call
            function_call = response.choices[0].message.function_call
            if function_call:
                entities = json.loads(function_call.arguments)
                # Remove chaves com valores None ou vazios
                return {k: v for k, v in entities.items() if v}

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")

        return {}

    def get_provider_name(self) -> str:
        """Retorna o nome do provedor."""
        return "openai"

    def _build_messages(
        self, prompt: str, context: ConversationContext
    ) -> list[dict]:
        """
        Constrói array de mensagens para a API OpenAI.

        Args:
            prompt: Mensagem atual do usuário
            context: Contexto da conversa

        Returns:
            Lista de mensagens formatadas
        """
        messages = []

        # System prompt
        system_prompt = self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # Histórico de conversa (últimas 10 mensagens)
        history = context.get_recent_messages(limit=10)
        for msg in history:
            messages.append(
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            )

        # Mensagem atual
        messages.append({"role": "user", "content": prompt})

        return messages

    async def _call_openai(
        self, messages: list[dict], model: str | None = None
    ) -> LLMResponse:
        """
        Chama a API OpenAI e processa resposta.

        Args:
            messages: Mensagens formatadas
            model: Modelo a usar (usa self.model se None)

        Returns:
            LLMResponse estruturado
        """
        model_to_use = model or self.model

        logger.info(f"Calling OpenAI with model: {model_to_use}")

        response = await self.client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            n=1,
        )

        # Extrai resposta
        choice = response.choices[0]
        content = choice.message.content or ""

        # Detecta intent e extrai entidades
        intent = await self.detect_intent(content)
        entities = await self.extract_entities(content, intent)

        # Calcula confidence (simplificado - baseado na finish_reason)
        confidence = 1.0 if choice.finish_reason == "stop" else 0.7

        # Conta tokens
        tokens_used = response.usage.total_tokens if response.usage else 0

        return LLMResponse(
            content=content,
            intent=intent,
            entities=entities,
            confidence=confidence,
            tokens_used=tokens_used,
            model_used=model_to_use,
            provider="openai",
            timestamp=datetime.now(timezone.utc),
        )

    async def _retry_with_backoff(
        self, messages: list[dict], max_retries: int = 3
    ) -> LLMResponse:
        """
        Retry com exponential backoff.

        Args:
            messages: Mensagens a enviar
            max_retries: Número máximo de tentativas

        Returns:
            LLMResponse

        Raises:
            Exception: Se falhar após todas as tentativas
        """
        import asyncio

        for attempt in range(max_retries):
            try:
                # Aguarda com backoff exponencial: 2^attempt segundos
                if attempt > 0:
                    wait_time = 2**attempt
                    logger.info(f"Waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)

                return await self._call_openai(messages)

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1} failed, trying again...")

        raise Exception("Failed after all retries")

    async def _try_fallback(self, messages: list[dict]) -> LLMResponse:
        """
        Tenta modelos de fallback.

        Args:
            messages: Mensagens a enviar

        Returns:
            LLMResponse

        Raises:
            Exception: Se todos os fallbacks falharem
        """
        for fallback_model in self.fallback_models:
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                return await self._call_openai(messages, model=fallback_model)
            except Exception as e:
                logger.warning(f"Fallback {fallback_model} failed: {e}")
                continue

        raise Exception("All fallback models failed")

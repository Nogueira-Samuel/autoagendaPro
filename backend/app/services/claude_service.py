"""
Claude Service

Implementação do serviço LLM usando Anthropic Claude.
Otimizado para conversas em português brasileiro.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from anthropic import AsyncAnthropic, APIError, RateLimitError, APIConnectionError

from app.config import settings
from app.services.llm_base import LLMServiceBase, LLMResponse, ConversationContext

logger = logging.getLogger(__name__)


class ClaudeService(LLMServiceBase):
    """
    Serviço de LLM usando Anthropic Claude.

    Utiliza o modelo Claude Sonnet com prompts otimizados para português.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        """
        Inicializa o serviço Claude.

        Args:
            api_key: API key da Anthropic (usa settings se None)
            model: Modelo a usar (usa settings se None)
            max_tokens: Máximo de tokens na resposta
            temperature: Temperature para geração (0-1)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.max_tokens = max_tokens or settings.CLAUDE_MAX_TOKENS
        self.temperature = temperature or settings.CLAUDE_TEMPERATURE

        # Cliente assíncrono Claude
        self.client = AsyncAnthropic(api_key=self.api_key)

        logger.info(f"Claude service initialized with model: {self.model}")

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
            Exception: Se falhar após tentativas de retry
        """
        # Constrói mensagens para API
        system_prompt = self._build_claude_system_prompt(context)
        messages = self._build_messages(prompt, context)

        # Tenta chamar Claude
        try:
            response = await self._call_claude(system_prompt, messages)
            return response
        except RateLimitError as e:
            logger.warning(f"Rate limit hit on Claude, retrying...")
            return await self._retry_with_backoff(system_prompt, messages)
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def detect_intent(self, message: str) -> str:
        """
        Detecta a intenção de uma mensagem.

        Args:
            message: Mensagem do usuário

        Returns:
            Intent: schedule, cancel, reschedule, inquiry, greeting, other
        """
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.1,
                system="Você detecta a intenção de mensagens sobre agendamentos. Responda apenas com uma palavra: schedule, cancel, reschedule, inquiry, greeting ou other.",
                messages=[{"role": "user", "content": message}],
            )

            # Extrai intent da resposta
            intent_text = response.content[0].text.strip().lower()

            # Valida intent
            valid_intents = [
                "schedule",
                "cancel",
                "reschedule",
                "inquiry",
                "greeting",
                "other",
            ]
            if intent_text in valid_intents:
                return intent_text

        except Exception as e:
            logger.error(f"Error detecting intent with Claude: {e}")

        # Fallback para keywords
        return self._parse_intent_from_response(message)

    async def extract_entities(self, message: str, intent: str) -> dict:
        """
        Extrai entidades de uma mensagem usando XML tags.

        Args:
            message: Mensagem do usuário
            intent: Intenção detectada

        Returns:
            Dicionário com entidades extraídas
        """
        try:
            extraction_prompt = f"""Extraia informações de agendamento desta mensagem.

Mensagem: {message}
Intenção: {intent}

Retorne no formato XML:
<entities>
<service>nome do serviço se mencionado</service>
<date>YYYY-MM-DD se mencionado</date>
<time>HH:MM se mencionado</time>
<customer_name>nome se mencionado</customer_name>
</entities>

Se alguma informação não estiver presente, omita a tag."""

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.1,
                messages=[{"role": "user", "content": extraction_prompt}],
            )

            # Extrai XML da resposta
            xml_text = response.content[0].text
            entities = self._parse_xml_entities(xml_text)

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities with Claude: {e}")
            return {}

    def get_provider_name(self) -> str:
        """Retorna o nome do provedor."""
        return "claude"

    def _build_claude_system_prompt(self, context: ConversationContext) -> str:
        """
        Constrói system prompt otimizado para Claude.

        Args:
            context: Contexto da conversa

        Returns:
            System prompt formatado com XML tags
        """
        system_prompt = f"""Você é um assistente de agendamentos inteligente para {context.business_name}.

<business_context>
<services>
{context.format_services_list()}
</services>

<business_hours>
{context.format_business_hours()}
</business_hours>

<timezone>{context.timezone}</timezone>
<max_advance_days>{context.max_advance_booking_days}</max_advance_days>
</business_context>

<instructions>
1. Converse naturalmente em português brasileiro
2. Identifique a intenção: agendar, cancelar, reagendar, perguntar informações
3. Colete informações necessárias: serviço, data, horário
4. Confirme disponibilidade antes de finalizar
5. Seja conciso: máximo 2-3 frases por resposta (WhatsApp)
6. Pergunte uma informação de cada vez se faltar dados
7. Seja sempre cordial e profissional
</instructions>

<response_guidelines>
- Use linguagem amigável mas profissional
- Confirme cada informação coletada
- Sugira alternativas se não houver disponibilidade
- Finalize com confirmação clara do agendamento
</response_guidelines>"""

        # Adiciona nome do cliente se conhecido
        if context.customer_name:
            system_prompt += f"\n\n<customer_name>{context.customer_name}</customer_name>"

        # Adiciona contexto adicional
        if context.additional_context:
            system_prompt += f"\n\n<additional_context>{context.additional_context}</additional_context>"

        return system_prompt

    def _build_messages(
        self, prompt: str, context: ConversationContext
    ) -> list[dict]:
        """
        Constrói array de mensagens para Claude API.

        Args:
            prompt: Mensagem atual
            context: Contexto da conversa

        Returns:
            Lista de mensagens formatadas
        """
        messages = []

        # Histórico de conversa
        history = context.get_recent_messages(limit=10)
        for msg in history:
            role = msg.get("role", "user")
            # Claude usa 'user' e 'assistant'
            if role not in ["user", "assistant"]:
                role = "user"

            messages.append({"role": role, "content": msg.get("content", "")})

        # Mensagem atual
        messages.append({"role": "user", "content": prompt})

        # Claude requer que mensagens alternem entre user/assistant
        # Se a última mensagem for assistant, remove
        if len(messages) > 0 and messages[-1]["role"] == "assistant":
            messages.pop()

        # Se não há mensagens ou primeira não é user, adiciona user placeholder
        if len(messages) == 0 or messages[0]["role"] != "user":
            messages.insert(0, {"role": "user", "content": "Olá"})

        return messages

    async def _call_claude(
        self, system_prompt: str, messages: list[dict]
    ) -> LLMResponse:
        """
        Chama a API Claude e processa resposta.

        Args:
            system_prompt: Prompt do sistema
            messages: Mensagens da conversa

        Returns:
            LLMResponse estruturado
        """
        logger.info(f"Calling Claude with {len(messages)} messages")

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=messages,
        )

        # Extrai conteúdo da resposta
        content = response.content[0].text if response.content else ""

        # Detecta intent e extrai entidades da resposta do usuário
        # (não da resposta do assistente)
        user_message = messages[-1]["content"] if messages else ""
        intent = await self.detect_intent(user_message)
        entities = await self.extract_entities(user_message, intent)

        # Calcula confidence (simplificado)
        confidence = 0.9 if response.stop_reason == "end_turn" else 0.7

        # Conta tokens
        tokens_used = (
            response.usage.input_tokens + response.usage.output_tokens
            if response.usage
            else 0
        )

        return LLMResponse(
            content=content,
            intent=intent,
            entities=entities,
            confidence=confidence,
            tokens_used=tokens_used,
            model_used=self.model,
            provider="claude",
            timestamp=datetime.now(timezone.utc),
        )

    async def _retry_with_backoff(
        self, system_prompt: str, messages: list[dict], max_retries: int = 3
    ) -> LLMResponse:
        """
        Retry com exponential backoff.

        Args:
            system_prompt: System prompt
            messages: Mensagens
            max_retries: Máximo de tentativas

        Returns:
            LLMResponse

        Raises:
            Exception: Se falhar após todas as tentativas
        """
        import asyncio

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2**attempt
                    logger.info(f"Waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)

                return await self._call_claude(system_prompt, messages)

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached: {e}")
                    raise
                logger.warning(f"Retry {attempt + 1} failed, trying again...")

        raise Exception("Failed after all retries")

    def _parse_xml_entities(self, xml_text: str) -> dict:
        """
        Extrai entidades de XML tags.

        Args:
            xml_text: Texto com XML tags

        Returns:
            Dicionário com entidades
        """
        entities = {}

        # Padrões para cada entidade
        patterns = {
            "service": r"<service>(.*?)</service>",
            "date": r"<date>(.*?)</date>",
            "time": r"<time>(.*?)</time>",
            "customer_name": r"<customer_name>(.*?)</customer_name>",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, xml_text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ["", "não mencionado", "n/a"]:
                    entities[key] = value

        return entities

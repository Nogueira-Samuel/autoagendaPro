"""
LLM Service Base

Classe abstrata base para todos os provedores de LLM (OpenAI, Claude, etc).
Define a interface comum para serviços de conversação com IA.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMResponse:
    """
    Resposta de um LLM com informações estruturadas.

    Attributes:
        content: Texto da resposta gerada
        intent: Intenção detectada (schedule, cancel, reschedule, inquiry, greeting, other)
        entities: Entidades extraídas (date, time, service, customer_name, etc)
        confidence: Confiança na detecção (0-1)
        tokens_used: Número de tokens utilizados
        model_used: Nome do modelo utilizado
        provider: Nome do provedor (openai, claude)
        timestamp: Timestamp da resposta
    """

    content: str
    intent: str | None = None
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    tokens_used: int = 0
    model_used: str = ""
    provider: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def has_intent(self, intent: str) -> bool:
        """Verifica se a resposta tem uma intenção específica."""
        return self.intent == intent

    def get_entity(self, key: str, default=None):
        """Obtém uma entidade extraída."""
        return self.entities.get(key, default)


@dataclass
class ConversationContext:
    """
    Contexto de uma conversa para o LLM.

    Contém todas as informações necessárias para o LLM gerar
    respostas contextualizadas e precisas.

    Attributes:
        tenant_id: ID do tenant (negócio)
        customer_phone: Telefone do cliente
        conversation_history: Histórico de mensagens (role: user/assistant, content: str)
        available_services: Lista de serviços disponíveis
        business_hours: Horários de funcionamento
        business_name: Nome do negócio
        timezone: Timezone do negócio
        customer_name: Nome do cliente (se conhecido)
        max_advance_booking_days: Dias máximos de antecedência
        buffer_time: Tempo de buffer entre agendamentos
        additional_context: Contexto adicional customizado
    """

    tenant_id: int
    customer_phone: str
    conversation_history: list[dict] = field(default_factory=list)
    available_services: list[dict] = field(default_factory=list)
    business_hours: dict = field(default_factory=dict)
    business_name: str = "AutoAgenda Pro"
    timezone: str = "America/Sao_Paulo"
    customer_name: str | None = None
    max_advance_booking_days: int = 30
    buffer_time: int = 0
    additional_context: dict = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        """
        Adiciona uma mensagem ao histórico.

        Args:
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
        """
        self.conversation_history.append({"role": role, "content": content})

    def get_recent_messages(self, limit: int = 10) -> list[dict]:
        """
        Obtém as mensagens mais recentes.

        Args:
            limit: Número máximo de mensagens

        Returns:
            Lista de mensagens recentes
        """
        return self.conversation_history[-limit:] if self.conversation_history else []

    def format_services_list(self) -> str:
        """
        Formata a lista de serviços para exibição.

        Returns:
            String formatada com serviços disponíveis
        """
        if not self.available_services:
            return "Nenhum serviço disponível"

        services_text = []
        for service in self.available_services:
            name = service.get("name", "")
            duration = service.get("duration_minutes", 0)
            price = service.get("price")

            service_line = f"- {name} ({duration} min"
            if price:
                service_line += f", R$ {price:.2f}"
            service_line += ")"

            services_text.append(service_line)

        return "\n".join(services_text)

    def format_business_hours(self) -> str:
        """
        Formata os horários de funcionamento.

        Returns:
            String formatada com horários
        """
        if not self.business_hours:
            return "Horários não configurados"

        days_pt = {
            "monday": "Segunda",
            "tuesday": "Terça",
            "wednesday": "Quarta",
            "thursday": "Quinta",
            "friday": "Sexta",
            "saturday": "Sábado",
            "sunday": "Domingo",
        }

        hours_text = []
        for day_en, day_pt in days_pt.items():
            day_hours = self.business_hours.get(day_en)
            if day_hours and day_hours.get("is_open", False):
                open_time = day_hours.get("open", "")
                close_time = day_hours.get("close", "")
                hours_text.append(f"{day_pt}: {open_time} - {close_time}")
            else:
                hours_text.append(f"{day_pt}: Fechado")

        return "\n".join(hours_text)


class LLMServiceBase(ABC):
    """
    Classe abstrata base para serviços de LLM.

    Define a interface que todos os provedores de LLM devem implementar.
    """

    @abstractmethod
    async def chat(
        self, prompt: str, context: ConversationContext
    ) -> LLMResponse:
        """
        Processa uma mensagem e retorna resposta.

        Args:
            prompt: Mensagem do usuário
            context: Contexto da conversa

        Returns:
            Resposta do LLM com intent e entities

        Raises:
            Exception: Em caso de erro na comunicação com o LLM
        """
        pass

    @abstractmethod
    async def detect_intent(self, message: str) -> str:
        """
        Detecta a intenção de uma mensagem.

        Args:
            message: Mensagem do usuário

        Returns:
            Intent detectado: schedule, cancel, reschedule, inquiry, greeting, other

        Raises:
            Exception: Em caso de erro
        """
        pass

    @abstractmethod
    async def extract_entities(self, message: str, intent: str) -> dict:
        """
        Extrai entidades de uma mensagem.

        Args:
            message: Mensagem do usuário
            intent: Intenção detectada

        Returns:
            Dicionário com entidades extraídas (service, date, time, etc)

        Raises:
            Exception: Em caso de erro
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retorna o nome do provedor.

        Returns:
            Nome do provedor (ex: 'openai', 'claude')
        """
        pass

    def _build_system_prompt(self, context: ConversationContext) -> str:
        """
        Constrói o prompt do sistema com contexto do negócio.

        Args:
            context: Contexto da conversa

        Returns:
            Prompt do sistema formatado
        """
        system_prompt = f"""Você é um assistente virtual de agendamentos para {context.business_name}.

CONTEXTO DO NEGÓCIO:
Serviços disponíveis:
{context.format_services_list()}

Horário de funcionamento:
{context.format_business_hours()}

Timezone: {context.timezone}
Agendamentos permitidos até: {context.max_advance_booking_days} dias no futuro

SUA MISSÃO:
1. Ser cordial e profissional em português brasileiro
2. Entender a intenção do cliente (agendar, cancelar, reagendar, informações)
3. Coletar informações necessárias: serviço desejado, data, horário
4. Confirmar disponibilidade antes de finalizar
5. Finalizar agendamento ou fornecer informações solicitadas

DIRETRIZES DE COMUNICAÇÃO:
- Use linguagem natural e amigável
- Confirme cada informação antes de prosseguir
- Se não houver disponibilidade, sugira alternativas próximas
- Seja breve nas respostas (máximo 2-3 frases para WhatsApp)
- Se o cliente não fornecer todas as informações, pergunte uma de cada vez
- Sempre confirme o agendamento antes de finalizar

EXEMPLO DE FLUXO:
Cliente: "Quero agendar"
Você: "Olá! Claro, posso ajudar. Qual serviço você deseja?"
Cliente: "Corte de cabelo"
Você: "Perfeito! Qual dia você prefere?"
Cliente: "Amanhã às 14h"
Você: "Verificando disponibilidade para amanhã às 14h... [confirmar ou sugerir alternativa]"
"""

        # Adiciona nome do cliente se conhecido
        if context.customer_name:
            system_prompt += f"\n\nNome do cliente: {context.customer_name}"

        # Adiciona contexto adicional se houver
        if context.additional_context:
            system_prompt += f"\n\nInformações adicionais: {context.additional_context}"

        return system_prompt

    def _format_conversation_history(self, history: list[dict]) -> str:
        """
        Formata o histórico de conversa para exibição.

        Args:
            history: Lista de mensagens (role, content)

        Returns:
            Histórico formatado
        """
        if not history:
            return "Nenhum histórico"

        formatted = []
        for msg in history:
            role = "Cliente" if msg.get("role") == "user" else "Assistente"
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _parse_intent_from_response(self, response: str) -> str:
        """
        Tenta extrair intent da resposta do LLM.

        Args:
            response: Resposta do LLM

        Returns:
            Intent detectado ou 'other'
        """
        response_lower = response.lower()

        # Palavras-chave para cada intent
        intent_keywords = {
            "schedule": ["agendar", "marcar", "reservar", "quero", "gostaria"],
            "cancel": ["cancelar", "desmarcar", "remover"],
            "reschedule": ["reagendar", "remarcar", "mudar", "trocar"],
            "inquiry": ["quanto", "preço", "horário", "funciona", "como"],
            "greeting": ["olá", "oi", "bom dia", "boa tarde", "boa noite"],
        }

        for intent, keywords in intent_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                return intent

        return "other"

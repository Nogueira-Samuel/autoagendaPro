"""
Conversation Manager

Gerencia o fluxo de conversação completo entre cliente e IA.
Coordena: LLM, banco de dados, validações e ações de agendamento.
"""

import logging
from datetime import datetime, date, time, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Tenant,
    Customer,
    Service,
    Appointment,
    Conversation,
    BusinessConfig,
    MessageDirection,
    MessageType,
    AppointmentStatus,
)
from app.services.llm_base import ConversationContext, LLMResponse
from app.services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Gerenciador de conversação para AutoAgenda Pro.

    Coordena todo o fluxo de processamento de mensagens:
    1. Carrega contexto do negócio
    2. Processa mensagem com LLM
    3. Executa ações (agendar, cancelar, etc)
    4. Salva histórico no banco
    5. Retorna resposta formatada
    """

    async def process_message(
        self, tenant_id: int, customer_phone: str, message: str, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Processa uma mensagem do WhatsApp.

        Este é o ponto de entrada principal para processar mensagens.

        Args:
            tenant_id: ID do tenant (negócio)
            customer_phone: Telefone do cliente
            message: Mensagem recebida
            db: Sessão do banco de dados

        Returns:
            Dicionário com resposta e metadados:
            {
                "response": str,  # Resposta a enviar
                "intent": str,    # Intenção detectada
                "entities": dict, # Entidades extraídas
                "action_taken": str | None,  # Ação executada
                "appointment_id": int | None,  # ID do agendamento criado
            }

        Raises:
            Exception: Em caso de erro no processamento
        """
        logger.info(
            f"Processing message for tenant {tenant_id}, customer {customer_phone}"
        )

        try:
            # 1. Carrega ou cria cliente
            customer = await self._get_or_create_customer(
                tenant_id, customer_phone, db
            )

            # 2. Carrega contexto da conversa
            context = await self._load_context(tenant_id, customer_phone, db)

            # 3. Adiciona mensagem atual ao contexto
            context.add_message("user", message)

            # 4. Processa com LLM
            llm_service = LLMFactory.create_from_tenant(
                await self._get_tenant(tenant_id, db)
            )
            llm_response: LLMResponse = await llm_service.chat(message, context)

            # 5. Executa ação baseada no intent
            action_result = await self._execute_action(
                tenant_id, customer.id, llm_response, db
            )

            # 6. Salva conversação no banco
            await self._save_conversation(
                tenant_id=tenant_id,
                customer_id=customer.id,
                user_message=message,
                assistant_message=llm_response.content,
                intent=llm_response.intent,
                entities=llm_response.entities,
                db=db,
            )

            # 7. Atualiza última interação do cliente
            customer.update_last_interaction()
            await db.commit()

            # 8. Retorna resposta estruturada
            return {
                "response": llm_response.content,
                "intent": llm_response.intent,
                "entities": llm_response.entities,
                "action_taken": action_result.get("action"),
                "appointment_id": action_result.get("appointment_id"),
                "confidence": llm_response.confidence,
                "tokens_used": llm_response.tokens_used,
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Retorna resposta de erro amigável
            return {
                "response": "Desculpe, houve um erro ao processar sua mensagem. Por favor, tente novamente.",
                "intent": "error",
                "entities": {},
                "action_taken": None,
                "appointment_id": None,
            }

    async def _load_context(
        self, tenant_id: int, customer_phone: str, db: AsyncSession
    ) -> ConversationContext:
        """
        Carrega contexto completo da conversa.

        Args:
            tenant_id: ID do tenant
            customer_phone: Telefone do cliente
            db: Sessão do banco

        Returns:
            ConversationContext preenchido
        """
        # Carrega tenant e config
        tenant = await self._get_tenant(tenant_id, db)
        config = await self._get_business_config(tenant_id, db)

        # Carrega serviços disponíveis
        services = await self._get_available_services(tenant_id, db)

        # Carrega histórico de conversa
        history = await self._get_conversation_history(
            tenant_id, customer_phone, db, limit=10
        )

        # Carrega nome do cliente se existir
        customer = await self._get_customer_by_phone(tenant_id, customer_phone, db)
        customer_name = customer.name if customer else None

        # Constrói contexto
        context = ConversationContext(
            tenant_id=tenant_id,
            customer_phone=customer_phone,
            conversation_history=history,
            available_services=services,
            business_hours=config.business_hours if config else {},
            business_name=tenant.name,
            timezone=tenant.timezone,
            customer_name=customer_name,
            max_advance_booking_days=config.max_advance_booking_days
            if config
            else 30,
            buffer_time=config.buffer_time if config else 0,
        )

        return context

    async def _get_conversation_history(
        self, tenant_id: int, customer_phone: str, db: AsyncSession, limit: int = 10
    ) -> list[dict]:
        """
        Obtém histórico de conversas do cliente.

        Args:
            tenant_id: ID do tenant
            customer_phone: Telefone do cliente
            db: Sessão do banco
            limit: Número máximo de mensagens

        Returns:
            Lista de mensagens [{role, content}]
        """
        # Busca cliente
        customer = await self._get_customer_by_phone(tenant_id, customer_phone, db)
        if not customer:
            return []

        # Busca conversas
        query = (
            select(Conversation)
            .where(Conversation.tenant_id == tenant_id)
            .where(Conversation.customer_id == customer.id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        conversations = result.scalars().all()

        # Formata histórico (mais recentes primeiro, depois inverte)
        history = []
        for conv in reversed(conversations):
            role = "user" if conv.direction == MessageDirection.INBOUND else "assistant"
            history.append({"role": role, "content": conv.content})

        return history

    async def _save_conversation(
        self,
        tenant_id: int,
        customer_id: int,
        user_message: str,
        assistant_message: str,
        intent: str | None,
        entities: dict,
        db: AsyncSession,
    ) -> None:
        """
        Salva mensagens da conversa no banco.

        Args:
            tenant_id: ID do tenant
            customer_id: ID do cliente
            user_message: Mensagem do usuário
            assistant_message: Resposta do assistente
            intent: Intenção detectada
            entities: Entidades extraídas
            db: Sessão do banco
        """
        # Salva mensagem do usuário
        user_conv = Conversation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            message_id=f"user_{datetime.now(timezone.utc).timestamp()}",
            direction=MessageDirection.INBOUND,
            message_type=MessageType.TEXT,
            content=user_message,
            intent=intent,
            context=entities,
            processed=True,
        )
        db.add(user_conv)

        # Salva resposta do assistente
        assistant_conv = Conversation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            message_id=f"assistant_{datetime.now(timezone.utc).timestamp()}",
            direction=MessageDirection.OUTBOUND,
            message_type=MessageType.TEXT,
            content=assistant_message,
            processed=True,
        )
        db.add(assistant_conv)

        await db.flush()

    async def _execute_action(
        self, tenant_id: int, customer_id: int, llm_response: LLMResponse, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Executa ação baseada no intent detectado.

        Args:
            tenant_id: ID do tenant
            customer_id: ID do cliente
            llm_response: Resposta do LLM
            db: Sessão do banco

        Returns:
            Resultado da ação {action, appointment_id, etc}
        """
        intent = llm_response.intent
        entities = llm_response.entities

        # Ação de agendamento
        if intent == "schedule":
            return await self._handle_schedule(
                tenant_id, customer_id, entities, db
            )

        # Ação de cancelamento
        elif intent == "cancel":
            return await self._handle_cancel(tenant_id, customer_id, entities, db)

        # Ação de reagendamento
        elif intent == "reschedule":
            return await self._handle_reschedule(
                tenant_id, customer_id, entities, db
            )

        # Sem ação necessária
        return {"action": None}

    async def _handle_schedule(
        self, tenant_id: int, customer_id: int, entities: dict, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Tenta criar um agendamento se todas as informações estiverem presentes.

        Args:
            tenant_id: ID do tenant
            customer_id: ID do cliente
            entities: Entidades extraídas (service, date, time)
            db: Sessão do banco

        Returns:
            Resultado da tentativa
        """
        # Verifica se tem todas as informações necessárias
        service_name = entities.get("service")
        date_str = entities.get("date")
        time_str = entities.get("time")

        if not all([service_name, date_str, time_str]):
            logger.info("Missing information for scheduling, need to collect more")
            return {"action": "collecting_info"}

        # Busca serviço
        service = await self._find_service_by_name(tenant_id, service_name, db)
        if not service:
            logger.warning(f"Service not found: {service_name}")
            return {"action": "service_not_found"}

        # Parse date e time
        try:
            appointment_date = datetime.fromisoformat(date_str).date()
            appointment_time = datetime.fromisoformat(f"{date_str} {time_str}").time()
        except Exception as e:
            logger.error(f"Error parsing date/time: {e}")
            return {"action": "invalid_datetime"}

        # Verifica disponibilidade
        is_available = await self._check_availability(
            tenant_id, service.id, appointment_date, appointment_time, db
        )

        if not is_available:
            return {"action": "not_available"}

        # Cria agendamento
        appointment = await self._create_appointment(
            tenant_id, customer_id, service.id, appointment_date, appointment_time, db
        )

        return {"action": "scheduled", "appointment_id": appointment.id}

    async def _handle_cancel(
        self, tenant_id: int, customer_id: int, entities: dict, db: AsyncSession
    ) -> dict[str, Any]:
        """Lógica de cancelamento (placeholder)."""
        # TODO: Implementar lógica de cancelamento
        return {"action": "cancel_pending"}

    async def _handle_reschedule(
        self, tenant_id: int, customer_id: int, entities: dict, db: AsyncSession
    ) -> dict[str, Any]:
        """Lógica de reagendamento (placeholder)."""
        # TODO: Implementar lógica de reagendamento
        return {"action": "reschedule_pending"}

    async def _check_availability(
        self,
        tenant_id: int,
        service_id: int,
        requested_date: date,
        requested_time: time,
        db: AsyncSession,
    ) -> bool:
        """
        Verifica se um horário está disponível.

        Args:
            tenant_id: ID do tenant
            service_id: ID do serviço
            requested_date: Data solicitada
            requested_time: Horário solicitado
            db: Sessão do banco

        Returns:
            True se disponível, False caso contrário
        """
        # Busca agendamentos existentes no mesmo horário
        query = (
            select(Appointment)
            .where(Appointment.tenant_id == tenant_id)
            .where(Appointment.scheduled_date == requested_date)
            .where(Appointment.scheduled_time == requested_time)
            .where(Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]))
        )

        result = await db.execute(query)
        existing = result.scalars().first()

        # Se já existe agendamento, não está disponível
        return existing is None

    async def _create_appointment(
        self,
        tenant_id: int,
        customer_id: int,
        service_id: int,
        scheduled_date: date,
        scheduled_time: time,
        db: AsyncSession,
    ) -> Appointment:
        """
        Cria um novo agendamento.

        Args:
            tenant_id: ID do tenant
            customer_id: ID do cliente
            service_id: ID do serviço
            scheduled_date: Data do agendamento
            scheduled_time: Horário do agendamento
            db: Sessão do banco

        Returns:
            Agendamento criado
        """
        # Busca serviço para pegar duração
        service = await db.get(Service, service_id)
        duration = service.duration_minutes if service else 60

        # Cria agendamento
        appointment = Appointment(
            tenant_id=tenant_id,
            customer_id=customer_id,
            service_id=service_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=duration,
            status=AppointmentStatus.PENDING,
        )

        db.add(appointment)
        await db.flush()

        logger.info(f"Appointment created: {appointment.id}")
        return appointment

    # Helper methods para buscar dados

    async def _get_tenant(self, tenant_id: int, db: AsyncSession) -> Tenant:
        """Busca tenant."""
        return await db.get(Tenant, tenant_id)

    async def _get_business_config(
        self, tenant_id: int, db: AsyncSession
    ) -> BusinessConfig | None:
        """Busca configuração do negócio."""
        query = select(BusinessConfig).where(BusinessConfig.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def _get_available_services(
        self, tenant_id: int, db: AsyncSession
    ) -> list[dict]:
        """Busca serviços disponíveis."""
        query = (
            select(Service)
            .where(Service.tenant_id == tenant_id)
            .where(Service.is_active == True)
        )
        result = await db.execute(query)
        services = result.scalars().all()

        return [
            {
                "id": s.id,
                "name": s.name,
                "duration_minutes": s.duration_minutes,
                "price": float(s.price) if s.price else None,
            }
            for s in services
        ]

    async def _get_customer_by_phone(
        self, tenant_id: int, phone: str, db: AsyncSession
    ) -> Customer | None:
        """Busca cliente por telefone."""
        query = (
            select(Customer)
            .where(Customer.tenant_id == tenant_id)
            .where(Customer.phone == phone)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def _get_or_create_customer(
        self, tenant_id: int, phone: str, db: AsyncSession
    ) -> Customer:
        """Obtém ou cria cliente."""
        customer = await self._get_customer_by_phone(tenant_id, phone, db)

        if not customer:
            customer = Customer(tenant_id=tenant_id, phone=phone)
            db.add(customer)
            await db.flush()
            logger.info(f"New customer created: {customer.id}")

        return customer

    async def _find_service_by_name(
        self, tenant_id: int, service_name: str, db: AsyncSession
    ) -> Service | None:
        """Busca serviço por nome (case-insensitive, fuzzy)."""
        query = (
            select(Service)
            .where(Service.tenant_id == tenant_id)
            .where(Service.is_active == True)
        )
        result = await db.execute(query)
        services = result.scalars().all()

        # Busca exata (case-insensitive)
        service_name_lower = service_name.lower()
        for service in services:
            if service.name.lower() == service_name_lower:
                return service

        # Busca parcial (contém)
        for service in services:
            if service_name_lower in service.name.lower():
                return service

        return None

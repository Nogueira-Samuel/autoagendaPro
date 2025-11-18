"""
Google Calendar Service

Serviço completo de integração com Google Calendar API.
Suporta multi-tenant com Service Account authentication.
"""

import asyncio
import logging
from datetime import datetime, date, time, timedelta
from typing import Any, TYPE_CHECKING

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.timezone_utils import (
    datetime_to_rfc3339,
    rfc3339_to_datetime,
    combine_date_time,
    parse_time_string,
    add_minutes,
    get_start_of_day,
    get_end_of_day,
    get_timezone,
    localize_datetime,
)

if TYPE_CHECKING:
    from app.models import Tenant

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class GoogleCalendarError(Exception):
    """Exceção base para erros do Google Calendar."""

    pass


class CalendarNotFoundError(GoogleCalendarError):
    """Calendário ou evento não encontrado."""

    pass


class CalendarConflictError(GoogleCalendarError):
    """Conflito de horário."""

    pass


class CalendarAuthenticationError(GoogleCalendarError):
    """Erro de autenticação."""

    pass


class CalendarRateLimitError(GoogleCalendarError):
    """Limite de rate excedido."""

    pass


# ============================================================================
# Google Calendar Service
# ============================================================================


class GoogleCalendarService:
    """
    Serviço de integração com Google Calendar API.

    Fornece operações CRUD para eventos, verificação de disponibilidade,
    e gerenciamento de calendário para multi-tenant system.

    Attributes:
        tenant_id: ID do tenant (para logging)
        credentials_json: Credenciais da Service Account
        calendar_id: ID do calendário do Google
        timezone: Timezone do calendário
        service: Instância do serviço Google Calendar API
    """

    # Scopes necessários para Google Calendar API
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(
        self,
        tenant_id: int,
        credentials_json: dict,
        calendar_id: str,
        timezone: str = "America/Sao_Paulo",
    ):
        """
        Inicializa o serviço Google Calendar para um tenant.

        Args:
            tenant_id: ID do tenant
            credentials_json: Dict com credenciais da Service Account
            calendar_id: ID do calendário (ex: "primary" ou email)
            timezone: Timezone do calendário (padrão: America/Sao_Paulo)

        Raises:
            CalendarAuthenticationError: Se credenciais inválidas
        """
        self.tenant_id = tenant_id
        self.credentials_json = credentials_json
        self.calendar_id = calendar_id
        self.timezone = timezone

        # Constrói serviço da API
        self.service = self._build_service()

        logger.info(
            f"Google Calendar service initialized for tenant {tenant_id}, "
            f"calendar: {calendar_id}, timezone: {timezone}"
        )

    def _build_service(self):
        """
        Constrói serviço Google Calendar API com Service Account.

        Returns:
            Resource do Google Calendar API

        Raises:
            CalendarAuthenticationError: Se falhar autenticação
        """
        try:
            # Cria credenciais da Service Account
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials_json, scopes=self.SCOPES
            )

            # Constrói serviço
            service = build("calendar", "v3", credentials=credentials)

            logger.debug(f"Google Calendar API service built for tenant {self.tenant_id}")
            return service

        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            raise CalendarAuthenticationError(
                f"Falha ao autenticar com Google Calendar: {e}"
            ) from e

    # ========================================================================
    # Event CRUD Operations
    # ========================================================================

    async def create_event(
        self,
        summary: str,
        description: str,
        start_datetime: datetime,
        end_datetime: datetime,
        attendee_email: str | None = None,
        location: str | None = None,
        send_notifications: bool = True,
    ) -> dict[str, Any]:
        """
        Cria um evento no Google Calendar.

        Args:
            summary: Título do evento (ex: "Consulta - Maria Silva")
            description: Descrição do evento
            start_datetime: Início (timezone-aware)
            end_datetime: Fim (timezone-aware)
            attendee_email: Email do participante (opcional)
            location: Local do evento (opcional)
            send_notifications: Enviar notificações (padrão: True)

        Returns:
            Dict com event_id, htmlLink, status

        Raises:
            GoogleCalendarError: Se falhar criação
            CalendarConflictError: Se houver conflito

        Examples:
            >>> service = GoogleCalendarService(...)
            >>> event = await service.create_event(
            ...     summary="Consulta - João",
            ...     description="Consulta médica",
            ...     start_datetime=datetime(...),
            ...     end_datetime=datetime(...),
            ...     attendee_email="joao@email.com"
            ... )
            >>> event['id']  # 'abc123xyz'
        """
        try:
            # Valida que datetimes têm timezone
            if start_datetime.tzinfo is None or end_datetime.tzinfo is None:
                raise ValueError("Datetimes devem ter timezone")

            # Constrói evento
            event_body = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": datetime_to_rfc3339(start_datetime),
                    "timeZone": self.timezone,
                },
                "end": {
                    "dateTime": datetime_to_rfc3339(end_datetime),
                    "timeZone": self.timezone,
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 30},
                        {"method": "email", "minutes": 60},
                    ],
                },
            }

            # Adiciona local se fornecido
            if location:
                event_body["location"] = location

            # Adiciona participante se fornecido
            if attendee_email:
                event_body["attendees"] = [{"email": attendee_email}]

            # Chama API (blocking - usa thread)
            event = await asyncio.to_thread(
                self.service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=event_body,
                    sendNotifications=send_notifications,
                )
                .execute
            )

            logger.info(
                f"Event created: {event['id']} for tenant {self.tenant_id} - {summary}"
            )

            return {
                "id": event["id"],
                "htmlLink": event.get("htmlLink"),
                "status": event.get("status"),
                "created": event.get("created"),
            }

        except HttpError as e:
            if e.resp.status == 409:
                raise CalendarConflictError(f"Conflito ao criar evento: {e}")
            elif e.resp.status == 429:
                raise CalendarRateLimitError(f"Rate limit excedido: {e}")
            else:
                logger.error(f"HTTP error creating event: {e}")
                raise GoogleCalendarError(f"Erro ao criar evento: {e}") from e

        except Exception as e:
            logger.error(f"Error creating event: {e}", exc_info=True)
            raise GoogleCalendarError(f"Erro ao criar evento: {e}") from e

    async def update_event(
        self,
        event_id: str,
        summary: str | None = None,
        description: str | None = None,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        location: str | None = None,
        send_notifications: bool = True,
    ) -> dict[str, Any]:
        """
        Atualiza um evento existente.

        Args:
            event_id: ID do evento no Google Calendar
            summary: Novo título (opcional)
            description: Nova descrição (opcional)
            start_datetime: Novo início (opcional)
            end_datetime: Novo fim (opcional)
            location: Novo local (opcional)
            send_notifications: Enviar notificações

        Returns:
            Dict do evento atualizado

        Raises:
            CalendarNotFoundError: Se evento não encontrado
            GoogleCalendarError: Outros erros
        """
        try:
            # Busca evento atual
            event = await asyncio.to_thread(
                self.service.events()
                .get(calendarId=self.calendar_id, eventId=event_id)
                .execute
            )

            # Atualiza campos fornecidos
            if summary is not None:
                event["summary"] = summary

            if description is not None:
                event["description"] = description

            if start_datetime is not None:
                event["start"] = {
                    "dateTime": datetime_to_rfc3339(start_datetime),
                    "timeZone": self.timezone,
                }

            if end_datetime is not None:
                event["end"] = {
                    "dateTime": datetime_to_rfc3339(end_datetime),
                    "timeZone": self.timezone,
                }

            if location is not None:
                event["location"] = location

            # Atualiza evento
            updated_event = await asyncio.to_thread(
                self.service.events()
                .update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=event,
                    sendNotifications=send_notifications,
                )
                .execute
            )

            logger.info(f"Event updated: {event_id} for tenant {self.tenant_id}")

            return updated_event

        except HttpError as e:
            if e.resp.status == 404:
                raise CalendarNotFoundError(f"Evento {event_id} não encontrado")
            else:
                logger.error(f"HTTP error updating event: {e}")
                raise GoogleCalendarError(f"Erro ao atualizar evento: {e}") from e

        except Exception as e:
            logger.error(f"Error updating event: {e}", exc_info=True)
            raise GoogleCalendarError(f"Erro ao atualizar evento: {e}") from e

    async def delete_event(
        self, event_id: str, send_notifications: bool = True
    ) -> bool:
        """
        Deleta um evento do calendário.

        Args:
            event_id: ID do evento
            send_notifications: Enviar notificações de cancelamento

        Returns:
            True se deletado com sucesso

        Raises:
            GoogleCalendarError: Se falhar deleção
        """
        try:
            await asyncio.to_thread(
                self.service.events()
                .delete(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    sendNotifications=send_notifications,
                )
                .execute
            )

            logger.info(f"Event deleted: {event_id} for tenant {self.tenant_id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                # Evento já foi deletado - retorna True
                logger.warning(f"Event {event_id} already deleted")
                return True
            elif e.resp.status == 410:
                # Gone - evento já foi deletado antes
                logger.warning(f"Event {event_id} was previously deleted")
                return True
            else:
                logger.error(f"HTTP error deleting event: {e}")
                raise GoogleCalendarError(f"Erro ao deletar evento: {e}") from e

        except Exception as e:
            logger.error(f"Error deleting event: {e}", exc_info=True)
            raise GoogleCalendarError(f"Erro ao deletar evento: {e}") from e

    async def get_event(self, event_id: str) -> dict[str, Any] | None:
        """
        Busca evento por ID.

        Args:
            event_id: ID do evento

        Returns:
            Dict do evento ou None se não encontrado
        """
        try:
            event = await asyncio.to_thread(
                self.service.events()
                .get(calendarId=self.calendar_id, eventId=event_id)
                .execute
            )

            return event

        except HttpError as e:
            if e.resp.status == 404:
                logger.debug(f"Event {event_id} not found")
                return None
            else:
                logger.error(f"HTTP error getting event: {e}")
                raise GoogleCalendarError(f"Erro ao buscar evento: {e}") from e

        except Exception as e:
            logger.error(f"Error getting event: {e}", exc_info=True)
            return None

    # ========================================================================
    # Availability Checking
    # ========================================================================

    async def check_availability(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_event_id: str | None = None,
    ) -> bool:
        """
        Verifica se um horário está disponível (sem conflitos).

        Args:
            start_datetime: Início do slot
            end_datetime: Fim do slot
            exclude_event_id: ID de evento a excluir (para reagendamento)

        Returns:
            True se disponível, False se houver conflito

        Examples:
            >>> available = await service.check_availability(
            ...     start_datetime=datetime(2024, 1, 15, 14, 0),
            ...     end_datetime=datetime(2024, 1, 15, 15, 0)
            ... )
            >>> available  # True ou False
        """
        try:
            # Busca eventos no período
            events = await self.list_events_in_range(
                start_datetime=start_datetime, end_datetime=end_datetime
            )

            # Filtra eventos (exclui se especificado)
            conflicting_events = [
                e
                for e in events
                if exclude_event_id is None or e["id"] != exclude_event_id
            ]

            # Se não há eventos, está disponível
            if not conflicting_events:
                return True

            # Verifica se há overlap
            for event in conflicting_events:
                event_start = rfc3339_to_datetime(event["start"]["dateTime"])
                event_end = rfc3339_to_datetime(event["end"]["dateTime"])

                if self._check_overlap(
                    start_datetime, end_datetime, event_start, event_end
                ):
                    logger.debug(
                        f"Conflict found with event {event['id']}: "
                        f"{event['summary']}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking availability: {e}", exc_info=True)
            # Em caso de erro, assume não disponível por segurança
            return False

    async def get_available_slots(
        self,
        date_obj: date,
        duration_minutes: int,
        business_hours: dict[str, Any],
        buffer_minutes: int = 0,
        slot_interval_minutes: int = 30,
    ) -> list[datetime]:
        """
        Obtém slots disponíveis para uma data específica.

        Args:
            date_obj: Data para verificar
            duration_minutes: Duração do agendamento
            business_hours: {'open': '09:00', 'close': '18:00', 'is_open': True}
            buffer_minutes: Buffer entre agendamentos
            slot_interval_minutes: Intervalo entre slots (padrão: 30 min)

        Returns:
            Lista de datetimes de início disponíveis

        Examples:
            >>> slots = await service.get_available_slots(
            ...     date_obj=date(2024, 1, 15),
            ...     duration_minutes=60,
            ...     business_hours={'open': '09:00', 'close': '18:00', 'is_open': True},
            ...     buffer_minutes=15
            ... )
            >>> slots  # [datetime(2024, 1, 15, 9, 0), ...]
        """
        available_slots = []

        # Verifica se está aberto neste dia
        if not business_hours.get("is_open", True):
            return available_slots

        # Parse horários de funcionamento
        open_time = parse_time_string(business_hours.get("open", "09:00"))
        close_time = parse_time_string(business_hours.get("close", "18:00"))

        # Cria datetime de início e fim do dia
        tz = get_timezone(self.timezone)
        current_slot = combine_date_time(date_obj, open_time, self.timezone)
        end_of_business = combine_date_time(date_obj, close_time, self.timezone)

        # Itera sobre possíveis slots
        while current_slot < end_of_business:
            # Calcula fim do slot (duração + buffer)
            slot_end = add_minutes(current_slot, duration_minutes + buffer_minutes)

            # Verifica se cabe no horário comercial
            if slot_end <= end_of_business:
                # Verifica disponibilidade
                is_available = await self.check_availability(current_slot, slot_end)

                if is_available:
                    available_slots.append(current_slot)

            # Próximo slot
            current_slot = add_minutes(current_slot, slot_interval_minutes)

        logger.debug(
            f"Found {len(available_slots)} available slots for {date_obj} "
            f"(tenant {self.tenant_id})"
        )

        return available_slots

    # ========================================================================
    # Event Listing
    # ========================================================================

    async def list_events(
        self,
        start_date: date,
        end_date: date,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Lista eventos em um período.

        Args:
            start_date: Data inicial
            end_date: Data final
            max_results: Máximo de eventos (padrão: 100)

        Returns:
            Lista de eventos

        Examples:
            >>> events = await service.list_events(
            ...     start_date=date(2024, 1, 1),
            ...     end_date=date(2024, 1, 31)
            ... )
        """
        try:
            # Converte dates para datetime com timezone
            start_dt = get_start_of_day(
                datetime.combine(start_date, time(0, 0)), self.timezone
            )
            end_dt = get_end_of_day(
                datetime.combine(end_date, time(23, 59)), self.timezone
            )

            return await self.list_events_in_range(
                start_datetime=start_dt,
                end_datetime=end_dt,
                max_results=max_results,
            )

        except Exception as e:
            logger.error(f"Error listing events: {e}", exc_info=True)
            return []

    async def list_events_in_range(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Lista eventos em um range de datetime.

        Args:
            start_datetime: Início do período
            end_datetime: Fim do período
            max_results: Máximo de eventos

        Returns:
            Lista de eventos
        """
        try:
            # Chama API
            events_result = await asyncio.to_thread(
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=datetime_to_rfc3339(start_datetime),
                    timeMax=datetime_to_rfc3339(end_datetime),
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute
            )

            events = events_result.get("items", [])

            logger.debug(
                f"Listed {len(events)} events for tenant {self.tenant_id} "
                f"({start_datetime.date()} to {end_datetime.date()})"
            )

            return events

        except HttpError as e:
            logger.error(f"HTTP error listing events: {e}")
            return []

        except Exception as e:
            logger.error(f"Error listing events: {e}", exc_info=True)
            return []

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _check_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime,
    ) -> bool:
        """
        Verifica se dois períodos se sobrepõem.

        Args:
            start1: Início do período 1
            end1: Fim do período 1
            start2: Início do período 2
            end2: Fim do período 2

        Returns:
            True se houver sobreposição

        Examples:
            >>> # 14:00-15:00 vs 14:30-15:30 = True (overlap)
            >>> # 14:00-15:00 vs 15:00-16:00 = False (no overlap)
        """
        return start1 < end2 and end1 > start2

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @staticmethod
    async def create_from_tenant(
        tenant: "Tenant", db: AsyncSession | None = None
    ) -> "GoogleCalendarService":
        """
        Cria serviço Google Calendar a partir de um tenant.

        Args:
            tenant: Instância do modelo Tenant
            db: Sessão do banco (para futura criptografia de credenciais)

        Returns:
            GoogleCalendarService configurado

        Raises:
            ValueError: Se tenant não tiver calendário configurado

        Examples:
            >>> tenant = await db.get(Tenant, tenant_id)
            >>> calendar_service = await GoogleCalendarService.create_from_tenant(tenant)
        """
        # Verifica se tenant tem calendário configurado
        if not tenant.has_google_calendar:
            raise ValueError(
                f"Tenant {tenant.id} ({tenant.name}) não tem Google Calendar configurado"
            )

        # Cria serviço
        return GoogleCalendarService(
            tenant_id=tenant.id,
            credentials_json=tenant.google_calendar_credentials,
            calendar_id=tenant.google_calendar_id,
            timezone=tenant.timezone,
        )

    @staticmethod
    def create_test_service(
        tenant_id: int = 1, calendar_id: str = "primary"
    ) -> "GoogleCalendarService":
        """
        Cria serviço de teste (para desenvolvimento).

        ATENÇÃO: Use apenas em desenvolvimento!

        Args:
            tenant_id: ID de teste
            calendar_id: Calendar ID de teste

        Returns:
            GoogleCalendarService para testes
        """
        # Credenciais de exemplo (não funcionam na prática)
        test_credentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        logger.warning("Creating TEST Google Calendar service - not for production!")

        return GoogleCalendarService(
            tenant_id=tenant_id,
            credentials_json=test_credentials,
            calendar_id=calendar_id,
            timezone="America/Sao_Paulo",
        )

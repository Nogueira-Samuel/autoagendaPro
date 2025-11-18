"""
Business Logic Services Package

Core services for AutoAgenda Pro:
- LLM conversational services (OpenAI, Claude)
- Conversation management
- Appointment scheduling logic
- Google Calendar integration
- Evolution API WhatsApp integration
"""

# LLM Base Classes
from app.services.llm_base import LLMServiceBase, LLMResponse, ConversationContext

# LLM Implementations
from app.services.openai_service import OpenAIService
from app.services.claude_service import ClaudeService

# LLM Factory and Pool
from app.services.llm_factory import (
    LLMFactory,
    LLMProvider,
    LLMServicePool,
    get_llm_pool,
)

# Conversation Manager
from app.services.conversation_manager import ConversationManager

# Google Calendar Service
from app.services.google_calendar_service import GoogleCalendarService

# WhatsApp Services
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
from app.services.whatsapp_service import EvolutionAPIService

__all__ = [
    # Base Classes
    "LLMServiceBase",
    "LLMResponse",
    "ConversationContext",
    # LLM Implementations
    "OpenAIService",
    "ClaudeService",
    # Factory and Pool
    "LLMFactory",
    "LLMProvider",
    "LLMServicePool",
    "get_llm_pool",
    # Conversation Manager
    "ConversationManager",
    # Google Calendar
    "GoogleCalendarService",
    # WhatsApp Base
    "WhatsAppServiceBase",
    "WhatsAppMessage",
    "WhatsAppResponse",
    "ConnectionStatus",
    "MediaType",
    "WhatsAppError",
    "WhatsAppConnectionError",
    "WhatsAppRateLimitError",
    "WhatsAppAuthenticationError",
    "WhatsAppMessageError",
    # WhatsApp Implementation
    "EvolutionAPIService",
]

"""
Business Logic Services Package

Core services for AutoAgenda Pro:
- LLM conversational services (OpenAI, Claude)
- Conversation management
- Appointment scheduling logic

Future services:
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
]

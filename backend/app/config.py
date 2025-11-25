"""
Configuration Settings

Gerenciamento centralizado de configurações usando Pydantic Settings.
Carrega variáveis de ambiente e fornece validação de tipos.
"""

from typing import Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação AutoAgenda Pro.

    Todas as configurações são carregadas de variáveis de ambiente.
    """

    # Application Settings
    APP_NAME: str = "AutoAgenda Pro"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "AI-powered WhatsApp appointment scheduling system"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    API_SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database Settings (Supabase PostgreSQL)
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL from Supabase")
    DB_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries for debugging")

    # Claude AI Settings (Anthropic)
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key for Claude AI")
    CLAUDE_MODEL: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model version")
    CLAUDE_MAX_TOKENS: int = Field(default=1024, description="Max tokens for Claude responses")
    CLAUDE_TEMPERATURE: float = Field(default=0.7, description="Temperature for Claude responses")

    # Evolution API Settings (WhatsApp)
    EVOLUTION_API_URL: str = Field(..., description="Evolution API base URL")
    EVOLUTION_API_KEY: str = Field(..., description="Evolution API authentication key")
    EVOLUTION_INSTANCE_NAME: str = Field(default="autoagenda", description="Evolution API instance name")

    # Redis Settings (for caching and session management)
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for caching")
    REDIS_CACHE_TTL: int = Field(default=3600, description="Redis cache TTL in seconds")

    # CORS Settings
    ALLOWED_ORIGINS: Union[str, list[str]] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )

    # Webhook Settings
    WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Secret for webhook validation")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="API rate limit per minute")
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")

    # Pagination Settings
    DEFAULT_PAGE_SIZE: int = Field(default=100, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=500, description="Maximum pagination page size")
    MIN_PAGE_SIZE: int = Field(default=1, description="Minimum pagination page size")

    # Webhook Settings (additional)
    WEBHOOK_MESSAGE_MAX_LENGTH: int = Field(default=10000, description="Maximum webhook message length")
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=30, description="Webhook request timeout")

    # Database Connection Settings (additional)
    DB_POOL_RECYCLE_SECONDS: int = Field(default=3600, description="Recycle DB connections after N seconds")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Verify connections before using")
    DB_CONNECT_TIMEOUT: int = Field(default=10, description="Database connection timeout in seconds")
    DB_RETRY_ATTEMPTS: int = Field(default=3, description="Number of retry attempts for DB operations")
    DB_RETRY_DELAY: float = Field(default=1.0, description="Delay between retry attempts in seconds")

    # HTTP Client Settings
    HTTP_TIMEOUT_SECONDS: int = Field(default=30, description="HTTP client timeout")
    HTTP_MAX_RETRIES: int = Field(default=3, description="Maximum HTTP request retries")

    # Security Settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_MAX_LENGTH: int = Field(default=72, description="Maximum password length (bcrypt limit)")
    JWT_SECRET_MIN_LENGTH: int = Field(default=32, description="Minimum JWT secret key length")

    # Notification Settings
    NOTIFICATION_REMINDER_24H: bool = Field(default=True, description="Enable 24-hour appointment reminders")
    NOTIFICATION_REMINDER_1H: bool = Field(default=True, description="Enable 1-hour appointment reminders")
    NOTIFICATION_CONFIRMATION: bool = Field(default=True, description="Enable appointment confirmation messages")
    NOTIFICATION_THANKS: bool = Field(default=True, description="Enable thank you messages after appointments")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """
        Parse ALLOWED_ORIGINS from string or list.

        Accepts:
        - "*" -> ["*"]  (wildcard for all origins)
        - "http://a.com,http://b.com" -> ["http://a.com", "http://b.com"]
        - ["http://a.com"] -> ["http://a.com"]  (already a list)

        Examples:
            >>> parse_allowed_origins("*")
            ["*"]
            >>> parse_allowed_origins("http://localhost:3000,http://localhost:8000")
            ["http://localhost:3000", "http://localhost:8000"]
        """
        if isinstance(v, str):
            # Handle wildcard
            if v.strip() == "*":
                return ["*"]
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # If already a list, return as-is
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Valida que o ambiente seja development, staging ou production."""
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valida o nível de log."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Retorna True se estiver em produção."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Retorna True se estiver em desenvolvimento."""
        return self.ENVIRONMENT == "development"


# Instância global de configurações
settings = Settings()


def get_settings() -> Settings:
    """
    Get settings instance.

    Useful for dependency injection in FastAPI routes.

    Example:
        @router.get("/config")
        async def get_config(settings: Settings = Depends(get_settings)):
            return {"app_name": settings.APP_NAME}
    """
    return settings

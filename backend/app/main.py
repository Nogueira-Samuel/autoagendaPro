"""
FastAPI Application Entry Point

Aplicação principal do AutoAgenda Pro - Sistema de agendamento via WhatsApp com IA.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import DatabaseManager, create_tables
from app.scheduler import start_scheduler, stop_scheduler

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.

    Startup: Inicializa conexões e recursos
    Shutdown: Limpa recursos e fecha conexões
    """
    # Startup
    logger.info("🚀 Starting AutoAgenda Pro...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    try:
        # Inicializa o banco de dados
        logger.info("📊 Initializing database connection...")
        DatabaseManager.get_engine()

        # Cria tabelas (apenas em desenvolvimento - use migrations em produção)
        if settings.is_development:
            logger.info("🔧 Creating database tables (development mode)...")
            await create_tables()

        # Inicia o scheduler de notificações
        logger.info("⏰ Starting notification scheduler...")
        start_scheduler()

        logger.info("✅ Application started successfully!")

        yield

    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down AutoAgenda Pro...")

        # Para o scheduler
        logger.info("⏰ Stopping notification scheduler...")
        stop_scheduler()

        # Fecha conexão com banco de dados
        await DatabaseManager.close()

        logger.info("✅ Application shutdown complete!")


# Inicializa a aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    # Disable docs in production for security
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)


# Configuração de CORS
# Validate CORS configuration for security
if "*" in settings.ALLOWED_ORIGINS:
    # Cannot use wildcard with credentials
    logger.warning(
        "SECURITY WARNING: Using wildcard (*) in ALLOWED_ORIGINS with "
        "allow_credentials=True is a security risk. Using specific origins only."
    )
    cors_origins = [
        origin for origin in settings.ALLOWED_ORIGINS if origin != "*"
    ]
else:
    cors_origins = settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Rate Limiting Middleware
from app.middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)
logger.info(f"Rate limiting {'enabled' if settings.RATE_LIMIT_ENABLED else 'disabled'}: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")


# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handler para exceções HTTP.
    """
    logger.error(
        f"HTTP error occurred: {exc.status_code} - {exc.detail} - Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler para erros de validação do Pydantic.
    """
    logger.error(f"Validation error: {exc.errors()} - Path: {request.url.path}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler para exceções não tratadas.
    """
    logger.exception(f"Unhandled error: {exc} - Path: {request.url.path}")

    # Em produção, não expõe detalhes do erro
    detail = str(exc) if settings.is_development else "Internal server error"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": detail,
            "status_code": 500,
        },
    )


# Health Check Endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Verifica o status da aplicação e suas dependências",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Endpoint de health check with dependency verification.

    Checks:
    - Application status
    - Database connectivity
    - Basic configuration

    Returns:
        dict: Status da aplicação e dependências
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database connectivity
    try:
        # Simple query to verify database is responding
        from sqlalchemy import text
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)[:100]}"

    # Check critical configuration
    try:
        if not settings.API_SECRET_KEY or len(settings.API_SECRET_KEY) < 32:
            health_status["checks"]["configuration"] = "warning: weak secret key"
        else:
            health_status["checks"]["configuration"] = "healthy"
    except Exception as e:
        health_status["checks"]["configuration"] = f"error: {str(e)}"

    return health_status


# Root Endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Root Endpoint",
    description="Informações básicas sobre a API",
)
async def root() -> dict[str, str]:
    """
    Endpoint raiz com informações da API.

    Returns:
        dict: Informações básicas da API
    """
    return {
        "message": "Welcome to AutoAgenda Pro API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Include API Routers
from app.routers import webhooks, appointments, customers, auth, notifications

app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX)
app.include_router(appointments.router, prefix=settings.API_V1_PREFIX)
app.include_router(customers.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )

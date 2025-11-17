"""
FastAPI Application Entry Point

Aplicação principal do AutoAgenda Pro - Sistema de agendamento via WhatsApp com IA.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import DatabaseManager, create_tables

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

        logger.info("✅ Application started successfully!")

        yield

    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down AutoAgenda Pro...")
        await DatabaseManager.close()
        logger.info("✅ Application shutdown complete!")


# Inicializa a aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)


# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


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
async def health_check() -> dict[str, str | bool]:
    """
    Endpoint de health check.

    Returns:
        dict: Status da aplicação
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


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
        "docs": "/docs" if not settings.is_production else "Documentation disabled in production",
    }


# TODO: Incluir routers quando forem criados
# from app.routers import webhooks, appointments, users
# app.include_router(webhooks.router, prefix=settings.API_V1_PREFIX, tags=["Webhooks"])
# app.include_router(appointments.router, prefix=settings.API_V1_PREFIX, tags=["Appointments"])
# app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )

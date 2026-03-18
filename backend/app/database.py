"""
Database Configuration

Configuração do SQLAlchemy com suporte assíncrono para PostgreSQL (Supabase).
"""

from typing import AsyncGenerator
from urllib.parse import urlparse, unquote
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.config import settings

# Base class para todos os models
Base = declarative_base()


class DatabaseManager:
    """
    Gerenciador de conexão com o banco de dados.

    Implementa padrão Singleton para garantir uma única instância do engine.
    """

    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """
        Retorna ou cria o engine do SQLAlchemy.

        Returns:
            AsyncEngine: Engine assíncrono do SQLAlchemy
        """
        if cls._engine is None:
            # Converte postgresql:// para postgresql+asyncpg://
            database_url = settings.DATABASE_URL
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
            elif not database_url.startswith("postgresql+asyncpg://"):
                raise ValueError(
                    "DATABASE_URL must start with postgresql:// or postgresql+asyncpg://"
                )

            parsed = urlparse(database_url)
            _host = parsed.hostname
            _port = parsed.port
            _user = unquote(parsed.username) if parsed.username else None
            _password = unquote(parsed.password) if parsed.password else None
            _database = parsed.path.lstrip("/")

            # Configuração do pool de conexões
            pool_class = NullPool if settings.ENVIRONMENT == "test" else QueuePool

            cls._engine = create_async_engine(
                database_url,
                echo=settings.DB_ECHO,
                poolclass=pool_class,
                pool_pre_ping=True,  # Verifica conexões antes de usar
                pool_recycle=3600,   # Recicla conexões após 1 hora
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                    "host": _host,
                    "port": _port,
                    "user": _user,
                    "password": _password,
                    "database": _database,
                }
            )

        return cls._engine

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        """
        Retorna ou cria a factory de sessões.

        Returns:
            async_sessionmaker: Factory para criar sessões assíncronas
        """
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                bind=cls.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

        return cls._session_factory

    @classmethod
    async def close(cls) -> None:
        """Fecha o engine e limpa os recursos."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter sessão do banco de dados.

    Uso em rotas FastAPI:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Sessão assíncrona do SQLAlchemy
    """
    session_factory = DatabaseManager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """
    Cria todas as tabelas no banco de dados.

    Nota: Em produção, use migrations (Alembic) ao invés desta função.
    """
    engine = DatabaseManager.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    Remove todas as tabelas do banco de dados.

    ATENÇÃO: Use apenas em desenvolvimento/testes!
    """
    if settings.is_production:
        raise RuntimeError("Cannot drop tables in production environment!")

    engine = DatabaseManager.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

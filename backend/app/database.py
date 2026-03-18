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
    _engine: AsyncEngine | None = None
    _session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if cls._engine is None:
            database_url = settings.DATABASE_URL

            raw_url = database_url
            if raw_url.startswith("postgresql+asyncpg://"):
                raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            elif not raw_url.startswith("postgresql://"):
                raise ValueError(
                    "DATABASE_URL must start with postgresql:// or postgresql+asyncpg://"
                )

            parsed = urlparse(raw_url)
            _host     = parsed.hostname
            _port     = parsed.port or 5432
            _user     = unquote(parsed.username) if parsed.username else None
            _password = unquote(parsed.password) if parsed.password else None
            _database = parsed.path.lstrip("/")

            clean_url = f"postgresql+asyncpg://{_host}:{_port}/{_database}?prepared_statement_cache_size=0&statement_cache_size=0"

            pool_class = NullPool if settings.ENVIRONMENT == "test" else QueuePool

            cls._engine = create_async_engine(
                clean_url,
                echo=settings.DB_ECHO,
                poolclass=pool_class,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    "host":     _host,
                    "port":     _port,
                    "user":     _user,
                    "password": _password,
                    "database": _database,
                    "statement_cache_size":          0,
                    "prepared_statement_cache_size": 0,
                },
            )

        return cls._engine

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker[AsyncSession]:
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
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
    engine = DatabaseManager.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    if settings.is_production:
        raise RuntimeError("Cannot drop tables in production environment!")
    engine = DatabaseManager.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

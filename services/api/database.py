import json
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import Text, TypeDecorator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from services.api.config import settings


class Base(DeclarativeBase):
    pass


class VectorType(TypeDecorator):
    """
    Dual-compatible vector type.
    Uses native pgvector if on PostgreSQL, or JSON string serialization on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 384, *args: Any, **kwargs: Any) -> None:
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dim))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            if dialect.name == "postgresql":
                return value
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

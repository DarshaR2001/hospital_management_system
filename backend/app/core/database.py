from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async database engine with NullPool for Supabase Pooler compatibility
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,
    connect_args={
        "ssl": "require",
    },
)


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
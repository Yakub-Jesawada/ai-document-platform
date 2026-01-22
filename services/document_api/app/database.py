from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from config import settings

# For PostgreSQL or other database systems (for production)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,           # Number of persistent connections
    max_overflow=20,        # Extra connections allowed above pool_size
    pool_timeout=30,        # Seconds to wait for a connection before error
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connection before using
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
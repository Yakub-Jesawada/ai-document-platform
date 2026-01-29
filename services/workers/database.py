from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
from workers.env import DATABASE_URL

# For PostgreSQL or other database systems (for production)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,           # Number of persistent connections
    max_overflow=20,        # Extra connections allowed above pool_size
    pool_timeout=30,        # Seconds to wait for a connection before error
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True,     # Test connection before using
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

Base = declarative_base()

@asynccontextmanager
async def get_kafka_db_session() -> AsyncSession:
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

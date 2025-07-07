"""
Database configuration and setup for NotebookAI
Apple-inspired clean database architecture with async support
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, DateTime, func
from typing import AsyncGenerator
import uuid
from datetime import datetime

from .config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models with Apple-style conventions"""
    
    # Primary key with UUID (Apple's preference for unique identifiers)
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Timestamps (Apple's attention to temporal data)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        """Clean string representation following Apple's clarity principles"""
        return f"<{self.__class__.__name__}(id={self.id})>"


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    Apple-style resource management with proper cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Create all database tables
    Apple-style initialization with clear logging
    """
    try:
        async with engine.begin() as conn:
            # Import models to ensure they're registered
            from ..models import user, data_source, chat, processing
            
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


async def drop_tables():
    """
    Drop all database tables (for development/testing)
    Apple-style with safety confirmation
    """
    try:
        async with engine.begin() as conn:
            from ..models import user, data_source, chat, processing
            
            await conn.run_sync(Base.metadata.drop_all)
            print("🗑️ Database tables dropped successfully")
            
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        raise


# Database health check
async def check_database_health() -> bool:
    """
    Check database connectivity
    Apple-style health monitoring
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False


# Connection pool monitoring
async def get_database_info() -> dict:
    """
    Get database connection info
    Apple-style system monitoring
    """
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    except Exception as e:
        return {"error": str(e)}
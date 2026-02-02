import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Use DATABASE_URL from environment (docker-compose) first
            # Convert postgresql:// to postgresql+asyncpg:// for async support
            database_url = os.getenv("DATABASE_URL", settings.database_url)

            if database_url:
                # Convert sync URL to async URL format
                if database_url.startswith("postgresql://"):
                    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                elif not database_url.startswith("postgresql+asyncpg://"):
                    database_url = f"postgresql+asyncpg://{database_url}"
            else:
                # Fallback to Supabase-style settings if DATABASE_URL not set
                database_url = f"postgresql+asyncpg://{getattr(settings, 'supabase_db_user', 'postgres')}:{getattr(settings, 'supabase_db_password', 'postgres')}@{getattr(settings, 'supabase_db_host', 'db')}:{getattr(settings, 'supabase_db_port', '5432')}/{getattr(settings, 'supabase_db_name', 'propertyflow')}"

            logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'configured'}")

            self.engine = create_async_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=20,  # Number of connections to maintain
                max_overflow=30,  # Additional connections when needed
                pool_pre_ping=True,  # Validate connections
                pool_recycle=3600,  # Recycle connections every hour
                echo=False  # Set to True for SQL debugging
            )

            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            logger.info("✅ Database connection pool initialized")
            
        except Exception as e:
            logger.error(f"❌ Database pool initialization failed: {e}")
            self.engine = None
            self.session_factory = None
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
    
    def get_session(self) -> AsyncSession:
        """Get database session from pool - returns async context manager"""
        if not self.session_factory:
            raise Exception("Database pool not initialized")
        return self.session_factory()

# Global database pool instance
db_pool = DatabasePool()

async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with db_pool.get_session() as session:
        yield session

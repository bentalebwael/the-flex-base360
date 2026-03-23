import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
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
            # FIX: Was using settings.supabase_db_user/password/host/port/name which don't exist
            # in the Settings class. Settings only has database_url (from DATABASE_URL in docker-compose).
            # The replace swaps the scheme to postgresql+asyncpg://, required by the async driver.
            database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # FIX: Removed poolclass=QueuePool — QueuePool is synchronous and incompatible
            # with create_async_engine. The default (AsyncAdaptedQueuePool) works correctly.
            self.engine = create_async_engine(
                database_url,
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
    
    # FIX: Was "async def", which returned a coroutine instead of the AsyncSession.
    # Since reservations.py does "async with db_pool.get_session() as session:", it needs
    # the AsyncSession directly (which is already an async context manager), not a coroutine.
    def get_session(self) -> AsyncSession:
        """Get database session from pool"""
        if not self.session_factory:
            raise Exception("Database pool not initialized")
        return self.session_factory()

# Global database pool instance
db_pool = DatabasePool()

async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with db_pool.get_session() as session:
        yield session

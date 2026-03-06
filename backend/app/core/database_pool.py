import asyncio
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
            # Create async engine with connection pooling
            # ملاحظة: تأكد أن supabase_db_password ليس None وإلا سيحدث خطأ في الـ URL
            db_pass = settings.supabase_db_password or ""
            database_url = f"postgresql+asyncpg://{settings.supabase_db_user}:{db_pass}@{settings.supabase_db_host}:{settings.supabase_db_port}/{settings.supabase_db_name}"
            
            self.engine = create_async_engine(
                database_url,
                # تم حذف poolclass=QueuePool لإصلاح خطأ الـ Async
                pool_size=settings.database_pool_size, # استخدام الإعدادات من config
                max_overflow=settings.database_max_overflow,
                pool_pre_ping=True,
                pool_recycle=settings.database_pool_recycle,
                echo=False
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # تجربة الاتصال للتأكد أن كل شيء يعمل
            async with self.engine.connect() as conn:
                await conn.run_sync(lambda sync_conn: None)
            
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

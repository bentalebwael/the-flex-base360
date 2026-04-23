# backend/app/core/database_pool.py:14-28 — Bug 3a (URL uses non-existent Settings fields)

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Create async engine with connection pooling
            database_url = f"postgresql+asyncpg://{settings.supabase_db_user}:{settings.supabase_db_password}@{settings.supabase_db_host}:{settings.supabase_db_port}/{settings.supabase_db_name}"
            
            self.engine = create_async_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=20,  # Number of connections to maintain
                max_overflow=30,  # Additional connections when needed
                pool_pre_ping=True,  # Validate connections
                pool_recycle=3600,  # Recycle connections every hour
                echo=False  # Set to True for SQL debugging
            )

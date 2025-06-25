"""
Database connection and session management
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
import asyncpg

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Global engine and session factory
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
asyncpg_pool: Optional[asyncpg.Pool] = None


async def get_database() -> asyncpg.Pool:
    """Get asyncpg connection pool for raw SQL operations"""
    global asyncpg_pool

    if asyncpg_pool is None:
        settings = get_settings()
        database_url = settings.database_url

        # Convert to asyncpg format if needed
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        asyncpg_pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        logger.info("AsyncPG pool created successfully")

    return asyncpg_pool


async def init_database():
    """Initialize database connection and create tables"""
    global engine, async_session_factory
    
    settings = get_settings()
    try:
        # Create async engine
        database_url = settings.database_url
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        engine = create_async_engine(
            database_url,
            pool_size=getattr(settings, 'database_pool_size', 10),
            max_overflow=getattr(settings, 'database_max_overflow', 20),
            echo=settings.debug,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
            )

        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Create session factory
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize asyncpg pool for raw SQL operations
        await get_database()

        # Create tables if they don't exist
        await create_tables()
        
        # Run any pending migrations
        await run_migrations()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_tables():
    """Create database tables"""
    global engine
    
    if engine is None:
        raise RuntimeError("Database engine not initialized")
    
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from src.database.models import (
                ConversationCheckpoint,
                ConversationWrite,
                ConversationMetric,
                AgentPerformanceLog,
                Conversation,
                Message,
                Customer
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def run_migrations():
    """Run database migrations if needed"""
    global engine
    
    if engine is None:
        raise RuntimeError("Database engine not initialized")
    
    try:
        async with engine.begin() as conn:
            # Check if migration tracking table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'schema_migrations'
                );
        """))
        
            migration_table_exists = result.scalar()
            
            if not migration_table_exists:
                # Create migration tracking table
                await conn.execute(text("""
                    CREATE TABLE schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """))
                
            # Check which migrations have been applied
            result = await conn.execute(text("SELECT version FROM schema_migrations"))
            applied_versions = {row[0] for row in result.fetchall()}
            
            # Apply migration 002 if not already applied
            if "002" not in applied_versions:
                await apply_migration_002(conn)
                await conn.execute(text("INSERT INTO schema_migrations (version) VALUES ('002')"))
                logger.info("Applied migration 002: checkpoint tables")
        
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


async def apply_migration_002(conn):
    """Apply migration 002: Add checkpoint tables"""
    
    migration_sql = """
    -- Table for storing conversation checkpoints
    CREATE TABLE IF NOT EXISTS conversation_checkpoints (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        thread_id VARCHAR(255) NOT NULL UNIQUE,
        checkpoint_data TEXT NOT NULL,
        custom_metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_conversation_checkpoints_thread_id 
    ON conversation_checkpoints(thread_id);

    CREATE INDEX IF NOT EXISTS idx_conversation_checkpoints_created_at 
    ON conversation_checkpoints(created_at);

    -- Table for storing conversation writes/operations
    CREATE TABLE IF NOT EXISTS conversation_writes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        thread_id VARCHAR(255) NOT NULL,
        task_id VARCHAR(255) NOT NULL,
        writes_data JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes for conversation writes
    CREATE INDEX IF NOT EXISTS idx_conversation_writes_thread_id 
    ON conversation_writes(thread_id);

    CREATE INDEX IF NOT EXISTS idx_conversation_writes_task_id 
    ON conversation_writes(task_id);

    CREATE INDEX IF NOT EXISTS idx_conversation_writes_created_at 
    ON conversation_writes(created_at);

    -- Table for storing conversation metrics and analytics
    CREATE TABLE IF NOT EXISTS conversation_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id VARCHAR(255) NOT NULL,
        metric_type VARCHAR(100) NOT NULL,
        metric_value DECIMAL(10,4),
        metric_data JSONB DEFAULT '{}',
        agent_type VARCHAR(100),
        recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes for conversation metrics
    CREATE INDEX IF NOT EXISTS idx_conversation_metrics_conversation_id 
    ON conversation_metrics(conversation_id);

    CREATE INDEX IF NOT EXISTS idx_conversation_metrics_type 
    ON conversation_metrics(metric_type);

    CREATE INDEX IF NOT EXISTS idx_conversation_metrics_agent_type 
    ON conversation_metrics(agent_type);

    CREATE INDEX IF NOT EXISTS idx_conversation_metrics_recorded_at 
    ON conversation_metrics(recorded_at);

    -- Table for agent performance tracking
    CREATE TABLE IF NOT EXISTS agent_performance_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_type VARCHAR(100) NOT NULL,
        conversation_id VARCHAR(255) NOT NULL,
        performance_data JSONB NOT NULL,
        execution_time_ms INTEGER,
        success BOOLEAN DEFAULT TRUE,
        error_message TEXT,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Indexes for agent performance log
    CREATE INDEX IF NOT EXISTS idx_agent_performance_log_agent_type 
    ON agent_performance_log(agent_type);

    CREATE INDEX IF NOT EXISTS idx_agent_performance_log_conversation_id 
    ON agent_performance_log(conversation_id);

    CREATE INDEX IF NOT EXISTS idx_agent_performance_log_timestamp 
    ON agent_performance_log(timestamp);

    CREATE INDEX IF NOT EXISTS idx_agent_performance_log_success 
    ON agent_performance_log(success);

    -- Add trigger to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    CREATE TRIGGER update_conversation_checkpoints_updated_at
        BEFORE UPDATE ON conversation_checkpoints
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    
    # Execute each statement separately
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
    
    for statement in statements:
        await conn.execute(text(statement))


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with proper error handling"""
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def get_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async with get_session() as session:
        yield session


async def close_database():
    """Close database connections"""
    global engine, async_session_factory, asyncpg_pool

    if engine:
        await engine.dispose()
        engine = None
    
    if asyncpg_pool:
        await asyncpg_pool.close()
        asyncpg_pool = None

    async_session_factory = None
    logger.info("Database connections closed")


async def health_check() -> dict:
    """Check database health"""
    if engine is None:
        return {"status": "error", "message": "Database not initialized"}
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as health_check"))
            result.scalar()
        
        return {"status": "healthy", "message": "Database connection successful"}
        
    except Exception as e:
        return {"status": "error", "message": f"Database health check failed: {str(e)}"}


# Utility functions for checkpoint management
async def save_checkpoint(thread_id: str, checkpoint_data: str, metadata: dict = None):
    """Save a conversation checkpoint"""
    async with get_session() as session:
        from src.database.models import ConversationCheckpoint
        
        # Check if checkpoint already exists
        existing = await session.get(ConversationCheckpoint, thread_id)
        
        if existing:
            existing.checkpoint_data = checkpoint_data
            existing.custom_metadata = metadata or {}
        else:
            checkpoint = ConversationCheckpoint(
                thread_id=thread_id,
                checkpoint_data=checkpoint_data,
                custom_metadata=metadata or {}
            )
            session.add(checkpoint)


async def load_checkpoint(thread_id: str) -> Optional[dict]:
    """Load a conversation checkpoint"""
    async with get_session() as session:
        from src.database.models import ConversationCheckpoint
        
        checkpoint = await session.get(ConversationCheckpoint, thread_id)
        
        if checkpoint:
            return {
                "thread_id": checkpoint.thread_id,
                "checkpoint_data": checkpoint.checkpoint_data,
                "metadata": checkpoint.custom_metadata,
                "created_at": checkpoint.created_at,
                "updated_at": checkpoint.updated_at
            }
        
        return None


async def cleanup_old_checkpoints(days: int = 30):
    """Clean up old checkpoints"""
    async with get_session() as session:
        cutoff_date = text(f"NOW() - INTERVAL '{days} days'")
        
        result = await session.execute(text(f"""
            DELETE FROM conversation_checkpoints 
            WHERE created_at < {cutoff_date}
        """))
        
        deleted_count = result.rowcount
        logger.info(f"Cleaned up {deleted_count} old checkpoints")
        
        return deleted_count

"""
Database reset script for development/testing
"""
import asyncio
import asyncpg
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from src.core.config import get_settings

async def reset_database():
    """Reset the database by dropping migration tracking and checkpoint tables"""
    settings = get_settings()
    database_url = settings.database_url
    
    # Convert to asyncpg format if needed
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        
        print("Dropping migration tracking and checkpoint tables...")
        
        # Drop tables in reverse dependency order
        tables_to_drop = [
            'agent_performance_log',
            'conversation_metrics', 
            'conversation_writes',
            'conversation_checkpoints',
            'schema_migrations'
        ]
        
        for table in tables_to_drop:
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        # Drop functions
        functions_to_drop = [
            'cleanup_old_conversation_data(INTEGER)',
            'update_updated_at_column()'
        ]
        
        for func in functions_to_drop:
            try:
                await conn.execute(f"DROP FUNCTION IF EXISTS {func} CASCADE;")
                print(f"Dropped function: {func}")
            except Exception as e:
                print(f"Error dropping function {func}: {e}")
        
        print("Database reset completed!")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    print("Resetting database...")
    success = asyncio.run(reset_database())
    if success:
        print("Database reset successful. You can now run your application.")
    else:
        print("Database reset failed.")
        sys.exit(1)
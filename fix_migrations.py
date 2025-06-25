"""
Fix migration tracking for existing database
"""
import asyncio
import asyncpg
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from src.core.config import get_settings

async def fix_migration_tracking():
    """Fix migration tracking for existing database"""
    settings = get_settings()
    database_url = settings.database_url
    
    # Convert to asyncpg format if needed
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        
        print("Fixing migration tracking...")
        
        # Check if migration tracking table exists
        migration_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'schema_migrations'
            );
        """)
        
        if not migration_exists:
            # Create migration tracking table
            await conn.execute("""
                CREATE TABLE schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            print("[OK] Created schema_migrations table")
        else:
            print("[OK] schema_migrations table already exists")
        
        # Check if checkpoint tables exist
        checkpoint_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'conversation_checkpoints'
            );
        """)
        
        if checkpoint_exists:
            # Check if migration 002 is already recorded
            migration_recorded = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM schema_migrations
                    WHERE version = '002'
                );
            """)
            
            if not migration_recorded:
                # Record that migration 002 has been applied
                await conn.execute("""
                    INSERT INTO schema_migrations (version) VALUES ('002');
                """)
                print("[OK] Marked migration 002 as applied")
            else:
                print("[OK] Migration 002 already recorded")
        else:
            print("[WARN] Checkpoint tables don't exist - they will be created on next startup")
        
        # Show final state
        print("\nFinal migration state:")
        migrations = await conn.fetch("SELECT version, applied_at FROM schema_migrations ORDER BY version;")
        if migrations:
            for migration in migrations:
                print(f"  - Version {migration['version']}: {migration['applied_at']}")
        else:
            print("  - No migrations recorded")
        
        print("\n[SUCCESS] Migration tracking fixed!")
        
    except Exception as e:
        print(f"[ERROR] Failed to fix migration tracking: {e}")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    print("Fixing migration tracking...")
    success = asyncio.run(fix_migration_tracking())
    if success:
        print("\nYou can now run your application normally.")
    else:
        print("\nFix failed. Check the error messages above.")
        sys.exit(1)
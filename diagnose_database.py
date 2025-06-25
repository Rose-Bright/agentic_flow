"""
Comprehensive database diagnostic script
"""
import asyncio
import asyncpg
import sys
import os
from datetime import datetime

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from src.core.config import get_settings

async def diagnose_database():
    """Run comprehensive database diagnostics"""
    settings = get_settings()
    database_url = settings.database_url
    
    print(f"=== Database Diagnostics - {datetime.now()} ===")
    print(f"Database URL: {database_url.replace(database_url.split('@')[0].split('//')[1], '***')}")
    
    # Convert to asyncpg format if needed
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = None
    try:
        print("\n1. Testing database connection...")
        conn = await asyncpg.connect(database_url)
        print("[OK] Database connection successful")
        
        print("\n2. Checking database version...")
        version = await conn.fetchval("SELECT version();")
        print(f"[OK] PostgreSQL version: {version.split(',')[0]}")
        
        print("\n3. Checking for existing tables...")
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        
        if tables:
            print("[OK] Existing tables:")
            for table in tables:
                print(f"  - {table['tablename']}")
        else:
            print("[WARN] No tables found")
        
        print("\n4. Checking for migration tracking table...")
        migration_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'schema_migrations'
            );
        """)
        
        if migration_exists:
            print("[OK] Migration tracking table exists")
            applied_migrations = await conn.fetch("SELECT version, applied_at FROM schema_migrations ORDER BY applied_at;")
            if applied_migrations:
                print("[OK] Applied migrations:")
                for migration in applied_migrations:
                    print(f"  - {migration['version']} (applied: {migration['applied_at']})")
            else:
                print("[WARN] No migrations recorded")
        else:
            print("[WARN] Migration tracking table does not exist")
        
        print("\n5. Checking for checkpoint tables...")
        checkpoint_tables = [
            'conversation_checkpoints',
            'conversation_writes', 
            'conversation_metrics',
            'agent_performance_log'
        ]
        
        for table in checkpoint_tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """)
            
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table};")
                print(f"[OK] {table} exists ({count} records)")
            else:
                print(f"[WARN] {table} does not exist")
        
        print("\n6. Checking for functions...")
        functions = await conn.fetch("""
            SELECT proname FROM pg_proc 
            WHERE proname IN ('update_updated_at_column', 'cleanup_old_conversation_data')
            AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
        """)
        
        if functions:
            print("[OK] Custom functions found:")
            for func in functions:
                print(f"  - {func['proname']}")
        else:
            print("[WARN] No custom functions found")
        
        print("\n7. Testing basic operations...")
        try:
            await conn.execute("SELECT gen_random_uuid();")
            print("[OK] UUID generation works")
        except Exception as e:
            print(f"[ERROR] UUID generation failed: {e}")
        
        try:
            await conn.execute("SELECT NOW();")
            print("[OK] Timestamp functions work")
        except Exception as e:
            print(f"[ERROR] Timestamp functions failed: {e}")
        
        print("\n8. Checking migration file...")
        migration_file = "src/database/migrations/002_add_checkpoint_tables.sql"
        if os.path.exists(migration_file):
            with open(migration_file, 'r') as f:
                migration_content = f.read()
            
            # Split into individual statements
            statements = [stmt.strip() for stmt in migration_content.split(';') if stmt.strip()]
            print(f"[OK] Migration file contains {len(statements)} statements")
            
            # Check for common issues
            if '$$' in migration_content:
                dollar_quote_count = migration_content.count('$$')
                if dollar_quote_count % 2 == 0:
                    print(f"[OK] Dollar-quoted strings properly closed ({dollar_quote_count//2} pairs)")
                else:
                    print(f"[ERROR] Unmatched dollar-quoted strings ({dollar_quote_count} total)")
            
        else:
            print(f"[ERROR] Migration file not found: {migration_file}")
        
        print("\n=== Diagnostic Summary ===")
        print("If you see any [ERROR] or [WARN] symbols above, those need to be addressed.")
        print("\nRecommended actions:")
        print("1. If checkpoint tables don't exist, run: python reset_database.py")
        print("2. Then restart your application to trigger migrations")
        print("3. Check your .env file for correct database credentials")
        
    except Exception as e:
        print(f"[ERROR] Database diagnostic failed: {e}")
        if "connection" in str(e).lower():
            print("\nConnection troubleshooting:")
            print("1. Check if PostgreSQL is running")
            print("2. Verify database credentials in .env file")
            print("3. Ensure database 'contact_center_db' exists")
            print("4. Check if user has proper permissions")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    asyncio.run(diagnose_database())
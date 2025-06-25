"""
Test application startup
"""
import sys
import os
import asyncio

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

async def test_startup():
    """Test the application startup sequence"""
    try:
        print("Testing application startup...")
        
        # Test database initialization
        print("1. Testing database initialization...")
        from src.database.connection import init_database
        await init_database()
        print("[OK] Database initialized")
        
        # Test LangGraph integration
        print("2. Testing LangGraph integration...")
        from src.core.langgraph_integration import get_langgraph_integration
        integration = await get_langgraph_integration()
        print("[OK] LangGraph integration initialized")
        
        # Test health check
        print("3. Testing health check...")
        health = await integration.health_check()
        print(f"[OK] Health status: {health['status']}")
        
        # Test cleanup
        print("4. Testing cleanup...")
        from src.core.langgraph_integration import cleanup_langgraph_integration
        await cleanup_langgraph_integration()
        print("[OK] Cleanup completed")
        
        print("\n[SUCCESS] All startup tests passed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    if not success:
        sys.exit(1)
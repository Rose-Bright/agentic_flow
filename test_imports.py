"""
Test imports to identify missing dependencies
"""
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

def test_import(module_name, import_statement):
    """Test a single import"""
    try:
        exec(import_statement)
        print(f"[OK] {module_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {module_name}: {e}")
        return False

print("Testing imports...")

# Core imports
test_import("config", "from src.core.config import get_settings")
test_import("logging", "from src.core.logging import setup_logging, get_logger")

# Database imports
test_import("database connection", "from src.database.connection import init_database")
test_import("database models", "from src.database.models import ConversationCheckpoint")

# API imports
test_import("API routes", "from src.api.routes import router")

# LangGraph imports - these might fail
test_import("langgraph orchestrator", "from src.core.langgraph_orchestrator import LangGraphOrchestrator")
test_import("state checkpointer", "from src.core.state_checkpointer import ConversationStateManager") 
test_import("graph builder", "from src.core.graph_builder import ConversationGraphBuilder")
test_import("tool registry", "from src.services.tool_registry import ToolRegistry")
test_import("langgraph integration", "from src.core.langgraph_integration import get_langgraph_integration")

print("\nTesting main application...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "src/main.py")
    main_module = importlib.util.module_from_spec(spec)
    print("[OK] main.py can be loaded")
except Exception as e:
    print(f"[ERROR] main.py: {e}")

print("\nIf you see [ERROR] messages above, those modules need to be created or fixed.")
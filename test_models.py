#!/usr/bin/env python3
"""
Test script to check if database models can be imported without errors
"""

import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

try:
    print("Testing model imports...")
    
    # Test base connection first
    from src.database.connection import Base
    print("SUCCESS: Base connection imported successfully")
    
    # Test individual models
    from src.database.models import (
        ConversationCheckpoint,
        ConversationWrite,
        Customer,
        Conversation,
        Message,
        ConversationMetric,
        AgentPerformanceLog
    )
    print("SUCCESS: All models imported successfully")
    
    # Test metadata access
    print(f"SUCCESS: Base metadata: {Base.metadata}")
    print(f"SUCCESS: Number of tables: {len(Base.metadata.tables)}")
    
    # List all table names
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    
    print("\nALL TESTS PASSED: Database models are working correctly!")
    
except Exception as e:
    print(f"ERROR: Error importing models: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
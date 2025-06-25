#!/usr/bin/env python3
"""
Test script to check application startup
"""

import sys
import os
import asyncio

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

async def test_startup():
    try:
        print("Testing application startup...")
        
        # Import main components
        from src.main import create_app
        from src.core.config import get_settings
        
        print("SUCCESS: Main components imported")
        
        # Create the app
        app = create_app()
        print("SUCCESS: FastAPI app created")
        
        # Get settings
        settings = get_settings()
        print(f"SUCCESS: Settings loaded - Debug: {settings.debug}")
        
        print("\nAPPLICATION STARTUP TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_startup())
    if result:
        print("\nAll startup tests passed - the metadata issue has been resolved!")
    else:
        print("\nStartup tests failed - there are still issues to fix.")
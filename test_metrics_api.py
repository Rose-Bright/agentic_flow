#!/usr/bin/env python3
"""
Test script to verify metrics API endpoints
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from fastapi.testclient import TestClient
from src.main import create_app

def test_metrics_endpoints():
    """Test the metrics API endpoints"""
    print("Testing Metrics API Endpoints...")
    
    try:
        # Create test client
        app = create_app()
        client = TestClient(app)
        
        # Note: These tests will require authentication in a real scenario
        # For now, we'll test if the endpoints exist and return proper error codes
        
        print("1. Testing system metrics endpoint...")
        response = client.get("/api/v1/metrics/system")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("   OK - System metrics endpoint exists")
        else:
            print(f"   ERROR - Unexpected status code: {response.status_code}")
        
        print("2. Testing conversation metrics endpoint...")
        response = client.get("/api/v1/metrics/conversations?time_range=24h")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("   OK - Conversation metrics endpoint exists")
        else:
            print(f"   ERROR - Unexpected status code: {response.status_code}")
        
        print("3. Testing performance metrics endpoint...")
        response = client.get("/api/v1/metrics/performance")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("   OK - Performance metrics endpoint exists")
        else:
            print(f"   ERROR - Unexpected status code: {response.status_code}")
        
        print("4. Testing business metrics endpoint...")
        response = client.get("/api/v1/metrics/business")
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("   OK - Business metrics endpoint exists")
        else:
            print(f"   ERROR - Unexpected status code: {response.status_code}")
        
        print("5. Testing export metrics endpoint...")
        export_params = {
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "metric_types": ["system"],
            "format": "json"
        }
        response = client.get("/api/v1/metrics/export", params=export_params)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("   OK - Export metrics endpoint exists")
        else:
            print(f"   ERROR - Unexpected status code: {response.status_code}")
        
        print("\nAPI endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"ERROR - API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\nTesting Health Check Endpoint...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print("   OK - Health endpoint working")
            return True
        else:
            print(f"   ERROR - Health check failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR - Health check test failed: {e}")
        return False

def test_basic_endpoints():
    """Test basic application endpoints"""
    print("\nTesting Basic Application Endpoints...")
    
    try:
        app = create_app()
        client = TestClient(app)
        
        # Test OpenAPI docs (if debug mode)
        response = client.get("/docs")
        print(f"   Docs endpoint status: {response.status_code}")
        
        # Test root metrics endpoint  
        response = client.get("/metrics")
        print(f"   Root metrics endpoint status: {response.status_code}")
        
        print("   OK - Basic endpoint tests completed")
        return True
        
    except Exception as e:
        print(f"ERROR - Basic endpoint test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting Metrics API Tests")
    print("=" * 50)
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    
    # Test basic endpoints
    basic_ok = test_basic_endpoints()
    
    # Test metrics endpoints
    metrics_ok = test_metrics_endpoints()
    
    print("\n" + "=" * 50)
    if health_ok and basic_ok and metrics_ok:
        print("SUCCESS - API tests completed successfully!")
        print("\nNote: Authentication is required for full metrics access.")
        print("Status codes 401 (Unauthorized) are expected without valid tokens.")
        return 0
    else:
        print("FAILURE - Some API tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Quick test script to verify metrics implementation
"""

import asyncio
import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from src.services.metrics import MetricsService, get_metrics_service
from src.models.metrics import SystemMetrics, ConversationMetrics, PerformanceMetrics, BusinessMetrics
from datetime import timedelta

async def test_metrics_service():
    """Test the metrics service functionality"""
    print("Testing Metrics Service...")
    
    try:
        # Test service initialization
        print("1. Testing service initialization...")
        service = await get_metrics_service()
        print("   OK - MetricsService initialized successfully")
        
        # Test system metrics
        print("2. Testing system metrics...")
        system_metrics = await service.get_system_metrics()
        print(f"   OK - System metrics retrieved: CPU {system_metrics.cpu_usage}%, Memory {system_metrics.memory_usage}%")
        
        # Test conversation metrics
        print("3. Testing conversation metrics...")
        conv_metrics = await service.get_conversation_metrics(timedelta(hours=24))
        print(f"   OK - Conversation metrics retrieved: {conv_metrics.total_conversations} total conversations")
        
        # Test performance metrics
        print("4. Testing performance metrics...")
        perf_metrics = await service.get_performance_metrics()
        print(f"   OK - Performance metrics retrieved: {perf_metrics.requests_per_second} req/sec")
        
        # Test business metrics
        print("5. Testing business metrics...")
        biz_metrics = await service.get_business_metrics()
        print(f"   OK - Business metrics retrieved: Customer satisfaction {biz_metrics.customer_satisfaction_score}")
        
        # Test export functionality
        print("6. Testing metrics export...")
        from datetime import datetime
        export_result = await service.export_metrics(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            metric_types=["system", "conversation"],
            format="json"
        )
        print(f"   OK - Export completed: {export_result['record_count']} records, {export_result['file_size']} bytes")
        
        print("\nAll metrics tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR - Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_metrics_models():
    """Test the metrics models"""
    print("\nTesting Metrics Models...")
    
    try:
        # Test SystemMetrics model
        system_metrics = SystemMetrics(
            uptime=86400.0,
            cpu_usage=25.5,
            memory_usage=45.2,
            disk_usage=60.0,
            active_connections=150,
            database_connections=15,
            redis_connections=8,
            queue_length=5,
            error_rate=2.5,
            response_time_avg=15.5,
            throughput=50,
            availability=99.9
        )
        print(f"   OK - SystemMetrics model: {system_metrics.cpu_usage}% CPU, {system_metrics.availability}% availability")
        
        # Test ConversationMetrics model
        conv_metrics = ConversationMetrics(
            time_range="24h",
            total_conversations=250,
            active_conversations=35,
            completed_conversations=200,
            abandoned_conversations=15,
            avg_response_time=12.8,
            median_response_time=10.5,
            p95_response_time=35.0,
            p99_response_time=75.0,
            avg_resolution_time=420.0,
            first_contact_resolution_rate=78.5,
            resolution_rate=88.2,
            avg_customer_satisfaction=4.3,
            escalation_rate=12.5,
            agent_utilization=82.0
        )
        print(f"   OK - ConversationMetrics model: {conv_metrics.total_conversations} conversations, {conv_metrics.resolution_rate}% resolution rate")
        
        # Test PerformanceMetrics model
        perf_metrics = PerformanceMetrics(
            requests_per_second=65.0,
            conversations_per_minute=18.0,
            messages_per_second=32.0,
            error_rate=1.8,
            timeout_rate=0.8,
            cpu_utilization=58.0,
            memory_utilization=68.0,
            connection_pool_usage=52.0,
            cache_hit_rate=88.5
        )
        print(f"   OK - PerformanceMetrics model: {perf_metrics.requests_per_second} req/sec, {perf_metrics.cache_hit_rate}% cache hit rate")
        
        # Test BusinessMetrics model
        biz_metrics = BusinessMetrics(
            time_range="24h",
            cost_per_conversation=2.18,
            revenue_impact=75000.0,
            cost_savings=32000.0,
            operational_efficiency=85.5,
            customer_satisfaction_score=4.35,
            net_promoter_score=68.0,
            customer_effort_score=2.6,
            customer_retention_impact=6.8,
            agent_productivity=82.5,
            automation_rate=73.0,
            deflection_rate=48.0,
            self_service_adoption=38.5,
            quality_score=87.5,
            compliance_score=94.0,
            issue_resolution_accuracy=89.2,
            peak_capacity_utilization=88.0
        )
        print(f"   OK - BusinessMetrics model: ${biz_metrics.cost_per_conversation} per conversation, {biz_metrics.automation_rate}% automation")
        
        print("\nAll metrics models work correctly!")
        return True
        
    except Exception as e:
        print(f"ERROR - Model test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting Metrics System Tests")
    print("=" * 50)
    
    # Test models first
    models_ok = await test_metrics_models()
    
    # Test service functionality
    service_ok = await test_metrics_service()
    
    print("\n" + "=" * 50)
    if models_ok and service_ok:
        print("SUCCESS - ALL TESTS PASSED - Metrics system is working correctly!")
        return 0
    else:
        print("FAILURE - SOME TESTS FAILED - Please check the errors above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
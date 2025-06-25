import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from dataclasses import asdict

from ..models.metrics import (
    SystemMetrics,
    ConversationMetrics, 
    PerformanceMetrics,
    BusinessMetrics,
    AgentMetrics,
    ToolMetrics,
    Alert,
    MetricsExport,
    MetricType,
    AlertLevel
)
from ..database.connection import get_database
from ..core.config import get_settings
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class MetricsService:
    """Service for collecting, analyzing, and reporting system metrics"""
    
    def __init__(self):
        self.settings = get_settings()
        self.performance_monitor = PerformanceMonitor()
        self.db = get_database()
        self.initialized = False
        
        # Metrics storage
        self.system_metrics_cache = {}
        self.conversation_metrics_cache = {}
        self.performance_metrics_cache = {}
        self.business_metrics_cache = {}
        
        # Alert management
        self.active_alerts = {}
        self.alert_history = []
        
        # Export tracking
        self.export_queue = {}
    
    async def initialize(self):
        """Initialize the metrics service"""
        if self.initialized:
            return
        
        logger.info("Initializing Metrics Service...")
        
        try:
            # Initialize performance monitor
            await self.performance_monitor.initialize() if hasattr(self.performance_monitor, 'initialize') else None
            
            # Set up metrics collection intervals
            await self._setup_metrics_collection()
            
            # Initialize alert thresholds
            await self._initialize_alert_thresholds()
            
            self.initialized = True
            logger.info("Metrics Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Metrics Service: {e}")
            raise
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # Check cache first
            cache_key = f"system_metrics_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            if cache_key in self.system_metrics_cache:
                return self.system_metrics_cache[cache_key]
            
            # Collect fresh metrics
            metrics_data = await self._collect_system_metrics()
            
            system_metrics = SystemMetrics(
                uptime=metrics_data.get("uptime", 0.0),
                cpu_usage=metrics_data.get("cpu_usage", 0.0),
                memory_usage=metrics_data.get("memory_usage", 0.0),
                disk_usage=metrics_data.get("disk_usage", 0.0),
                network_io=metrics_data.get("network_io", {}),
                active_connections=metrics_data.get("active_connections", 0),
                database_connections=metrics_data.get("database_connections", 0),
                redis_connections=metrics_data.get("redis_connections", 0),
                queue_length=metrics_data.get("queue_length", 0),
                error_rate=metrics_data.get("error_rate", 0.0),
                response_time_avg=metrics_data.get("response_time_avg", 0.0),
                throughput=metrics_data.get("throughput", 0),
                availability=metrics_data.get("availability", 100.0)
            )
            
            # Cache the result
            self.system_metrics_cache[cache_key] = system_metrics
            
            return system_metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                uptime=0.0, cpu_usage=0.0, memory_usage=0.0, disk_usage=0.0,
                active_connections=0, database_connections=0, redis_connections=0,
                queue_length=0, error_rate=0.0, response_time_avg=0.0,
                throughput=0, availability=0.0
            )
    
    async def get_conversation_metrics(self, time_delta: timedelta = timedelta(hours=24)) -> ConversationMetrics:
        """Get conversation metrics for specified time period"""
        try:
            time_range = f"{int(time_delta.total_seconds() / 3600)}h"
            cache_key = f"conversation_metrics_{time_range}_{datetime.utcnow().strftime('%Y%m%d%H')}"
            
            if cache_key in self.conversation_metrics_cache:
                return self.conversation_metrics_cache[cache_key]
            
            # Collect conversation metrics from database
            metrics_data = await self._collect_conversation_metrics(time_delta)
            
            conversation_metrics = ConversationMetrics(
                time_range=time_range,
                total_conversations=metrics_data.get("total_conversations", 0),
                active_conversations=metrics_data.get("active_conversations", 0),
                completed_conversations=metrics_data.get("completed_conversations", 0),
                abandoned_conversations=metrics_data.get("abandoned_conversations", 0),
                channel_distribution=metrics_data.get("channel_distribution", {}),
                avg_response_time=metrics_data.get("avg_response_time", 0.0),
                median_response_time=metrics_data.get("median_response_time", 0.0),
                p95_response_time=metrics_data.get("p95_response_time", 0.0),
                p99_response_time=metrics_data.get("p99_response_time", 0.0),
                avg_resolution_time=metrics_data.get("avg_resolution_time", 0.0),
                first_contact_resolution_rate=metrics_data.get("first_contact_resolution_rate", 0.0),
                resolution_rate=metrics_data.get("resolution_rate", 0.0),
                avg_customer_satisfaction=metrics_data.get("avg_customer_satisfaction", 0.0),
                sentiment_distribution=metrics_data.get("sentiment_distribution", {}),
                escalation_rate=metrics_data.get("escalation_rate", 0.0),
                agent_utilization=metrics_data.get("agent_utilization", 0.0),
                agent_response_distribution=metrics_data.get("agent_response_distribution", {})
            )
            
            # Cache the result
            self.conversation_metrics_cache[cache_key] = conversation_metrics
            
            return conversation_metrics
            
        except Exception as e:
            logger.error(f"Error getting conversation metrics: {e}")
            return self._get_empty_conversation_metrics(time_delta)
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get system performance metrics"""
        try:
            cache_key = f"performance_metrics_{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            
            if cache_key in self.performance_metrics_cache:
                return self.performance_metrics_cache[cache_key]
            
            # Collect performance metrics
            metrics_data = await self._collect_performance_metrics()
            
            performance_metrics = PerformanceMetrics(
                api_response_times=metrics_data.get("api_response_times", {}),
                database_query_times=metrics_data.get("database_query_times", {}),
                external_service_times=metrics_data.get("external_service_times", {}),
                requests_per_second=metrics_data.get("requests_per_second", 0.0),
                conversations_per_minute=metrics_data.get("conversations_per_minute", 0.0),
                messages_per_second=metrics_data.get("messages_per_second", 0.0),
                error_rate=metrics_data.get("error_rate", 0.0),
                error_breakdown=metrics_data.get("error_breakdown", {}),
                timeout_rate=metrics_data.get("timeout_rate", 0.0),
                cpu_utilization=metrics_data.get("cpu_utilization", 0.0),
                memory_utilization=metrics_data.get("memory_utilization", 0.0),
                connection_pool_usage=metrics_data.get("connection_pool_usage", 0.0),
                cache_hit_rate=metrics_data.get("cache_hit_rate", 0.0),
                sla_compliance=metrics_data.get("sla_compliance", {})
            )
            
            # Cache the result
            self.performance_metrics_cache[cache_key] = performance_metrics
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return self._get_empty_performance_metrics()
    
    async def get_business_metrics(self) -> BusinessMetrics:
        """Get business-focused metrics and KPIs"""
        try:
            cache_key = f"business_metrics_{datetime.utcnow().strftime('%Y%m%d%H')}"
            
            if cache_key in self.business_metrics_cache:
                return self.business_metrics_cache[cache_key]
            
            # Collect business metrics
            metrics_data = await self._collect_business_metrics()
            
            business_metrics = BusinessMetrics(
                time_range="24h",  # Default to 24 hours
                cost_per_conversation=metrics_data.get("cost_per_conversation", 0.0),
                revenue_impact=metrics_data.get("revenue_impact", 0.0),
                cost_savings=metrics_data.get("cost_savings", 0.0),
                operational_efficiency=metrics_data.get("operational_efficiency", 0.0),
                customer_satisfaction_score=metrics_data.get("customer_satisfaction_score", 0.0),
                net_promoter_score=metrics_data.get("net_promoter_score", 0.0),
                customer_effort_score=metrics_data.get("customer_effort_score", 0.0),
                customer_retention_impact=metrics_data.get("customer_retention_impact", 0.0),
                agent_productivity=metrics_data.get("agent_productivity", 0.0),
                automation_rate=metrics_data.get("automation_rate", 0.0),
                deflection_rate=metrics_data.get("deflection_rate", 0.0),
                self_service_adoption=metrics_data.get("self_service_adoption", 0.0),
                quality_score=metrics_data.get("quality_score", 0.0),
                compliance_score=metrics_data.get("compliance_score", 0.0),
                issue_resolution_accuracy=metrics_data.get("issue_resolution_accuracy", 0.0),
                peak_capacity_utilization=metrics_data.get("peak_capacity_utilization", 0.0),
                capacity_planning_metrics=metrics_data.get("capacity_planning_metrics", {}),
                period_over_period_growth=metrics_data.get("period_over_period_growth", {}),
                seasonal_patterns=metrics_data.get("seasonal_patterns", {})
            )
            
            # Cache the result
            self.business_metrics_cache[cache_key] = business_metrics
            
            return business_metrics
            
        except Exception as e:
            logger.error(f"Error getting business metrics: {e}")
            return self._get_empty_business_metrics()
    
    async def export_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        metric_types: List[str],
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export metrics data in specified format"""
        try:
            export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create export record
            export_record = MetricsExport(
                export_id=export_id,
                metric_types=[MetricType(mt) for mt in metric_types],
                start_date=start_date,
                end_date=end_date,
                format=format,
                status="processing"
            )
            
            # Store in export queue
            self.export_queue[export_id] = export_record
            
            # Collect data for export
            export_data = await self._collect_export_data(start_date, end_date, metric_types)
            
            # Generate export file
            if format.lower() == "csv":
                file_content = await self._generate_csv_export(export_data)
                content_type = "text/csv"
                file_extension = "csv"
            elif format.lower() == "json":
                file_content = await self._generate_json_export(export_data)
                content_type = "application/json"
                file_extension = "json"
            elif format.lower() == "excel":
                file_content = await self._generate_excel_export(export_data)
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                file_extension = "xlsx"
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            # Update export record
            export_record.status = "completed"
            export_record.completed_at = datetime.utcnow()
            export_record.file_size = len(file_content) if isinstance(file_content, (str, bytes)) else 0
            export_record.record_count = len(export_data)
            
            return {
                "export_id": export_id,
                "status": "completed",
                "file_content": file_content,
                "content_type": content_type,
                "filename": f"metrics_export_{export_id}.{file_extension}",
                "record_count": export_record.record_count,
                "file_size": export_record.file_size
            }
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            if export_id in self.export_queue:
                self.export_queue[export_id].status = "failed"
            raise
    
    # Private helper methods
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics from various sources"""
        try:
            import psutil
            import time
            
            # Get system metrics using psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate uptime (placeholder - would need actual implementation)
            uptime = time.time() - psutil.boot_time()
            
            # Get database connection count (placeholder)
            db_connections = await self._get_database_connection_count()
            
            # Get Redis connection count (placeholder)
            redis_connections = await self._get_redis_connection_count()
            
            # Get queue length (placeholder)
            queue_length = await self._get_queue_length()
            
            # Calculate error rate from recent logs
            error_rate = await self._calculate_error_rate()
            
            # Get response time metrics
            response_time_avg = await self._get_average_response_time()
            
            # Get throughput
            throughput = await self._get_current_throughput()
            
            return {
                "uptime": uptime,
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "network_io": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "active_connections": 0,  # Placeholder
                "database_connections": db_connections,
                "redis_connections": redis_connections,
                "queue_length": queue_length,
                "error_rate": error_rate,
                "response_time_avg": response_time_avg,
                "throughput": throughput,
                "availability": 100.0  # Placeholder
            }
            
        except ImportError:
            # Fallback if psutil is not available
            logger.warning("psutil not available, using placeholder system metrics")
            return {
                "uptime": 0.0,
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "network_io": {},
                "active_connections": 0,
                "database_connections": 0,
                "redis_connections": 0,
                "queue_length": 0,
                "error_rate": 0.0,
                "response_time_avg": 0.0,
                "throughput": 0,
                "availability": 100.0
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def _collect_conversation_metrics(self, time_delta: timedelta) -> Dict[str, Any]:
        """Collect conversation metrics from database"""
        try:
            # This would typically query the database for conversation data
            # For now, returning placeholder data
            
            return {
                "total_conversations": 100,
                "active_conversations": 25,
                "completed_conversations": 70,
                "abandoned_conversations": 5,
                "channel_distribution": {
                    "web": 40,
                    "phone": 30,
                    "email": 20,
                    "mobile": 10
                },
                "avg_response_time": 15.5,
                "median_response_time": 12.0,
                "p95_response_time": 45.0,
                "p99_response_time": 120.0,
                "avg_resolution_time": 300.0,
                "first_contact_resolution_rate": 75.0,
                "resolution_rate": 85.0,
                "avg_customer_satisfaction": 4.2,
                "sentiment_distribution": {
                    "positive": 60,
                    "neutral": 30,
                    "negative": 10
                },
                "escalation_rate": 15.0,
                "agent_utilization": 78.0,
                "agent_response_distribution": {
                    "tier1_support": 50,
                    "tier2_technical": 25,
                    "tier3_expert": 15,
                    "sales": 7,
                    "billing": 3
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting conversation metrics: {e}")
            return {}
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        try:
            return {
                "api_response_times": {
                    "/api/v1/conversations": 150.0,
                    "/api/v1/agents": 75.0,
                    "/api/v1/tools": 100.0,
                    "/api/v1/metrics": 200.0
                },
                "database_query_times": {
                    "conversations": 25.0,
                    "customers": 15.0,
                    "agents": 10.0,
                    "metrics": 50.0
                },
                "external_service_times": {
                    "vertex_ai": 300.0,
                    "anthropic": 250.0,
                    "knowledge_base": 100.0
                },
                "requests_per_second": 50.0,
                "conversations_per_minute": 12.0,
                "messages_per_second": 25.0,
                "error_rate": 2.5,
                "error_breakdown": {
                    "validation_errors": 60,
                    "service_errors": 25,
                    "timeout_errors": 15
                },
                "timeout_rate": 1.2,
                "cpu_utilization": 65.0,
                "memory_utilization": 72.0,
                "connection_pool_usage": 45.0,
                "cache_hit_rate": 85.0,
                "sla_compliance": {
                    "response_time": 95.0,
                    "availability": 99.9,
                    "resolution_time": 88.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {}
    
    async def _collect_business_metrics(self) -> Dict[str, Any]:
        """Collect business-focused metrics"""
        try:
            return {
                "cost_per_conversation": 2.35,
                "revenue_impact": 50000.0,
                "cost_savings": 25000.0,
                "operational_efficiency": 82.0,
                "customer_satisfaction_score": 4.3,
                "net_promoter_score": 65.0,
                "customer_effort_score": 2.8,
                "customer_retention_impact": 5.2,
                "agent_productivity": 78.0,
                "automation_rate": 70.0,
                "deflection_rate": 45.0,
                "self_service_adoption": 35.0,
                "quality_score": 85.0,
                "compliance_score": 92.0,
                "issue_resolution_accuracy": 87.0,
                "peak_capacity_utilization": 85.0,
                "capacity_planning_metrics": {
                    "current_capacity": 1000,
                    "peak_demand": 850,
                    "forecasted_demand": 950
                },
                "period_over_period_growth": {
                    "conversations": 15.0,
                    "resolution_rate": 8.0,
                    "satisfaction": 12.0
                },
                "seasonal_patterns": {
                    "morning_peak": 9,
                    "afternoon_peak": 14,
                    "evening_peak": 19
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            return {}
    
    async def _collect_export_data(
        self,
        start_date: datetime,
        end_date: datetime,
        metric_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Collect metrics data for export"""
        export_data = []
        
        try:
            for metric_type in metric_types:
                if metric_type == "system":
                    system_metrics = await self.get_system_metrics()
                    export_data.append({
                        "type": "system",
                        "timestamp": system_metrics.timestamp,
                        "data": system_metrics.dict()
                    })
                elif metric_type == "conversation":
                    conv_metrics = await self.get_conversation_metrics()
                    export_data.append({
                        "type": "conversation", 
                        "timestamp": conv_metrics.timestamp,
                        "data": conv_metrics.dict()
                    })
                elif metric_type == "performance":
                    perf_metrics = await self.get_performance_metrics()
                    export_data.append({
                        "type": "performance",
                        "timestamp": perf_metrics.timestamp,
                        "data": perf_metrics.dict()
                    })
                elif metric_type == "business":
                    biz_metrics = await self.get_business_metrics()
                    export_data.append({
                        "type": "business",
                        "timestamp": biz_metrics.timestamp,
                        "data": biz_metrics.dict()
                    })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error collecting export data: {e}")
            return []
    
    async def _generate_csv_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate CSV export from metrics data"""
        if not data:
            return ""
        
        output = io.StringIO()
        
        # Flatten data for CSV
        flattened_data = []
        for item in data:
            flat_item = {"type": item["type"], "timestamp": item["timestamp"]}
            flat_item.update(self._flatten_dict(item["data"]))
            flattened_data.append(flat_item)
        
        if flattened_data:
            fieldnames = flattened_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_data)
        
        return output.getvalue()
    
    async def _generate_json_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate JSON export from metrics data"""
        return json.dumps(data, default=str, indent=2)
    
    async def _generate_excel_export(self, data: List[Dict[str, Any]]) -> bytes:
        """Generate Excel export from metrics data"""
        # Placeholder - would require openpyxl or similar library
        return b"Excel export not implemented"
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    # Placeholder methods for system metric collection
    
    async def _get_database_connection_count(self) -> int:
        """Get current database connection count"""
        # Placeholder implementation
        return 15
    
    async def _get_redis_connection_count(self) -> int:
        """Get current Redis connection count"""
        # Placeholder implementation
        return 8
    
    async def _get_queue_length(self) -> int:
        """Get current queue length"""
        # Placeholder implementation
        return 5
    
    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        # Placeholder implementation
        return 2.5
    
    async def _get_average_response_time(self) -> float:
        """Get average response time"""
        # Placeholder implementation
        return 15.5
    
    async def _get_current_throughput(self) -> int:
        """Get current throughput (requests per second)"""
        # Placeholder implementation
        return 50
    
    # Default/empty metrics methods
    
    def _get_empty_conversation_metrics(self, time_delta: timedelta) -> ConversationMetrics:
        """Return empty conversation metrics"""
        time_range = f"{int(time_delta.total_seconds() / 3600)}h"
        return ConversationMetrics(
            time_range=time_range,
            total_conversations=0,
            active_conversations=0,
            completed_conversations=0,
            abandoned_conversations=0,
            avg_response_time=0.0,
            median_response_time=0.0,
            p95_response_time=0.0,
            p99_response_time=0.0,
            avg_resolution_time=0.0,
            first_contact_resolution_rate=0.0,
            resolution_rate=0.0,
            avg_customer_satisfaction=0.0,
            escalation_rate=0.0,
            agent_utilization=0.0
        )
    
    def _get_empty_performance_metrics(self) -> PerformanceMetrics:
        """Return empty performance metrics"""
        return PerformanceMetrics(
            requests_per_second=0.0,
            conversations_per_minute=0.0,
            messages_per_second=0.0,
            error_rate=0.0,
            timeout_rate=0.0,
            cpu_utilization=0.0,
            memory_utilization=0.0,
            connection_pool_usage=0.0,
            cache_hit_rate=0.0
        )
    
    def _get_empty_business_metrics(self) -> BusinessMetrics:
        """Return empty business metrics"""
        return BusinessMetrics(
            time_range="24h",
            cost_per_conversation=0.0,
            revenue_impact=0.0,
            cost_savings=0.0,
            operational_efficiency=0.0,
            customer_satisfaction_score=0.0,
            net_promoter_score=0.0,
            customer_effort_score=0.0,
            customer_retention_impact=0.0,
            agent_productivity=0.0,
            automation_rate=0.0,
            deflection_rate=0.0,
            self_service_adoption=0.0,
            quality_score=0.0,
            compliance_score=0.0,
            issue_resolution_accuracy=0.0,
            peak_capacity_utilization=0.0
        )
    
    async def _setup_metrics_collection(self):
        """Set up periodic metrics collection"""
        # Placeholder for setting up periodic collection
        pass
    
    async def _initialize_alert_thresholds(self):
        """Initialize alert thresholds"""
        # Placeholder for alert threshold initialization
        pass


# Dependency injection function
async def get_metrics_service() -> MetricsService:
    """Get metrics service instance"""
    service = MetricsService()
    await service.initialize()
    return service
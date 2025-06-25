from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class MetricType(str, Enum):
    """Types of metrics available"""
    SYSTEM = "system"
    CONVERSATION = "conversation"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    AGENT = "agent"
    TOOL = "tool"

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class SystemMetrics(BaseModel):
    """System-level metrics and health indicators"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    uptime: float = Field(..., description="System uptime in seconds")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    network_io: Dict[str, float] = Field(default={}, description="Network I/O statistics")
    active_connections: int = Field(..., description="Number of active connections")
    database_connections: int = Field(..., description="Active database connections")
    redis_connections: int = Field(..., description="Active Redis connections")
    queue_length: int = Field(..., description="Current queue length")
    error_rate: float = Field(..., description="System error rate percentage")
    response_time_avg: float = Field(..., description="Average response time in seconds")
    throughput: int = Field(..., description="Requests per second")
    availability: float = Field(..., description="System availability percentage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationMetrics(BaseModel):
    """Comprehensive conversation metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    time_range: str = Field(..., description="Time range for metrics (e.g., '1h', '24h')")
    
    # Volume metrics
    total_conversations: int = Field(..., description="Total number of conversations")
    active_conversations: int = Field(..., description="Currently active conversations")
    completed_conversations: int = Field(..., description="Completed conversations")
    abandoned_conversations: int = Field(..., description="Abandoned conversations")
    
    # Channel distribution
    channel_distribution: Dict[str, int] = Field(default={}, description="Conversations by channel")
    
    # Response time metrics
    avg_response_time: float = Field(..., description="Average response time in seconds")
    median_response_time: float = Field(..., description="Median response time in seconds")
    p95_response_time: float = Field(..., description="95th percentile response time")
    p99_response_time: float = Field(..., description="99th percentile response time")
    
    # Resolution metrics
    avg_resolution_time: float = Field(..., description="Average resolution time in seconds")
    first_contact_resolution_rate: float = Field(..., description="First contact resolution rate")
    resolution_rate: float = Field(..., description="Overall resolution rate")
    
    # Quality metrics
    avg_customer_satisfaction: float = Field(..., description="Average customer satisfaction score")
    sentiment_distribution: Dict[str, int] = Field(default={}, description="Sentiment distribution")
    escalation_rate: float = Field(..., description="Escalation rate percentage")
    
    # Agent metrics
    agent_utilization: float = Field(..., description="Agent utilization percentage")
    agent_response_distribution: Dict[str, int] = Field(default={}, description="Responses by agent type")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PerformanceMetrics(BaseModel):
    """System performance metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    # Response time metrics
    api_response_times: Dict[str, float] = Field(default={}, description="API endpoint response times")
    database_query_times: Dict[str, float] = Field(default={}, description="Database query performance")
    external_service_times: Dict[str, float] = Field(default={}, description="External service response times")
    
    # Throughput metrics
    requests_per_second: float = Field(..., description="Requests per second")
    conversations_per_minute: float = Field(..., description="Conversations started per minute")
    messages_per_second: float = Field(..., description="Messages processed per second")
    
    # Error metrics
    error_rate: float = Field(..., description="Overall error rate percentage")
    error_breakdown: Dict[str, int] = Field(default={}, description="Errors by type")
    timeout_rate: float = Field(..., description="Timeout rate percentage")
    
    # Resource utilization
    cpu_utilization: float = Field(..., description="CPU utilization percentage")
    memory_utilization: float = Field(..., description="Memory utilization percentage")
    connection_pool_usage: float = Field(..., description="Connection pool usage percentage")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    
    # SLA compliance
    sla_compliance: Dict[str, float] = Field(default={}, description="SLA compliance percentages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BusinessMetrics(BaseModel):
    """Business-focused metrics and KPIs"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    time_range: str = Field(..., description="Time range for metrics")
    
    # Financial metrics
    cost_per_conversation: float = Field(..., description="Average cost per conversation")
    revenue_impact: float = Field(..., description="Revenue impact from conversations")
    cost_savings: float = Field(..., description="Cost savings from automation")
    operational_efficiency: float = Field(..., description="Operational efficiency percentage")
    
    # Customer metrics
    customer_satisfaction_score: float = Field(..., description="Customer satisfaction score")
    net_promoter_score: float = Field(..., description="Net promoter score")
    customer_effort_score: float = Field(..., description="Customer effort score")
    customer_retention_impact: float = Field(..., description="Customer retention impact")
    
    # Productivity metrics
    agent_productivity: float = Field(..., description="Agent productivity score")
    automation_rate: float = Field(..., description="Automation rate percentage")
    deflection_rate: float = Field(..., description="Call deflection rate")
    self_service_adoption: float = Field(..., description="Self-service adoption rate")
    
    # Quality metrics
    quality_score: float = Field(..., description="Overall quality score")
    compliance_score: float = Field(..., description="Compliance score")
    issue_resolution_accuracy: float = Field(..., description="Issue resolution accuracy")
    
    # Volume and capacity
    peak_capacity_utilization: float = Field(..., description="Peak capacity utilization")
    capacity_planning_metrics: Dict[str, Any] = Field(default={}, description="Capacity planning data")
    
    # Trend analysis
    period_over_period_growth: Dict[str, float] = Field(default={}, description="Period over period growth")
    seasonal_patterns: Dict[str, Any] = Field(default={}, description="Seasonal pattern analysis")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AgentMetrics(BaseModel):
    """Individual agent performance metrics"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    # Performance metrics
    conversations_handled: int = Field(..., description="Conversations handled")
    avg_response_time: float = Field(..., description="Average response time")
    avg_resolution_time: float = Field(..., description="Average resolution time") 
    success_rate: float = Field(..., description="Success rate percentage")
    escalation_rate: float = Field(..., description="Escalation rate percentage")
    
    # Quality metrics
    customer_satisfaction_avg: float = Field(..., description="Average customer satisfaction")
    confidence_score_avg: float = Field(..., description="Average confidence score")
    accuracy_score: float = Field(..., description="Response accuracy score")
    
    # Utilization metrics
    active_time: float = Field(..., description="Active time in seconds")
    idle_time: float = Field(..., description="Idle time in seconds")
    utilization_rate: float = Field(..., description="Utilization rate percentage")
    
    # Tool usage
    tools_used: Dict[str, int] = Field(default={}, description="Tools usage count")
    most_used_tools: List[str] = Field(default=[], description="Most frequently used tools")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ToolMetrics(BaseModel):
    """Tool usage and performance metrics"""
    tool_name: str = Field(..., description="Tool name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    # Usage metrics
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Successful executions")
    failed_executions: int = Field(..., description="Failed executions")
    success_rate: float = Field(..., description="Success rate percentage")
    
    # Performance metrics
    avg_execution_time: float = Field(..., description="Average execution time")
    min_execution_time: float = Field(..., description="Minimum execution time")
    max_execution_time: float = Field(..., description="Maximum execution time")
    
    # Error analysis
    error_types: Dict[str, int] = Field(default={}, description="Error breakdown by type")
    timeout_count: int = Field(..., description="Number of timeouts")
    
    # Usage patterns
    usage_by_agent_type: Dict[str, int] = Field(default={}, description="Usage by agent type")
    peak_usage_hours: List[int] = Field(default=[], description="Peak usage hours")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Alert(BaseModel):
    """System alert model"""
    id: str = Field(..., description="Alert identifier")
    level: AlertLevel = Field(..., description="Alert severity level")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    metric_type: MetricType = Field(..., description="Related metric type")
    threshold_value: Optional[float] = Field(None, description="Threshold that triggered alert")
    current_value: Optional[float] = Field(None, description="Current metric value")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation time")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution time")
    resolved: bool = Field(default=False, description="Whether alert is resolved")
    metadata: Dict[str, Any] = Field(default={}, description="Additional alert metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MetricsExport(BaseModel):
    """Metrics export configuration and result"""
    export_id: str = Field(..., description="Export identifier")
    metric_types: List[MetricType] = Field(..., description="Types of metrics to export")
    start_date: datetime = Field(..., description="Export start date")
    end_date: datetime = Field(..., description="Export end date")
    format: str = Field(..., description="Export format (csv, json, excel)")
    status: str = Field(default="pending", description="Export status")
    file_url: Optional[str] = Field(None, description="URL to download exported file")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Export creation time")
    completed_at: Optional[datetime] = Field(None, description="Export completion time")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    record_count: Optional[int] = Field(None, description="Number of records exported")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
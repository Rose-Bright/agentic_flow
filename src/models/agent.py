from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentType(str, Enum):
    INTENT_CLASSIFIER = "intent_classifier"
    TIER1_SUPPORT = "tier1_support"
    TIER2_TECHNICAL = "tier2_technical"
    TIER3_EXPERT = "tier3_expert"
    SALES = "sales"
    BILLING = "billing"
    SUPERVISOR = "supervisor"

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

class AgentCapability(BaseModel):
    """Model representing an agent's capability"""
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    confidence_threshold: float = Field(..., description="Minimum confidence threshold")
    requires_tools: List[str] = Field(default=[], description="Required tools for this capability")
    supported_languages: List[str] = Field(default=["en"], description="Supported languages")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class AgentConfiguration(BaseModel):
    """Model for agent configuration"""
    agent_type: AgentType = Field(..., description="Type of agent")
    model_name: str = Field(..., description="Name of the AI model to use")
    model_version: str = Field(..., description="Version of the AI model")
    capabilities: List[AgentCapability] = Field(..., description="Agent capabilities")
    max_concurrent_conversations: int = Field(default=10, description="Maximum concurrent conversations")
    response_timeout: int = Field(default=30, description="Response timeout in seconds")
    escalation_threshold: float = Field(default=0.7, description="Confidence threshold for escalation")
    tools_allowed: List[str] = Field(default=[], description="Tools this agent can use")
    metadata: Dict[str, Any] = Field(default={}, description="Additional configuration")

class AgentMetrics(BaseModel):
    """Model for agent metrics"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    total_conversations: int = Field(default=0, description="Total conversations handled")
    active_conversations: int = Field(default=0, description="Currently active conversations")
    avg_response_time: float = Field(default=0.0, description="Average response time in seconds")
    avg_resolution_time: float = Field(default=0.0, description="Average resolution time in seconds")
    successful_resolutions: int = Field(default=0, description="Number of successful resolutions")
    escalation_count: int = Field(default=0, description="Number of escalations")
    avg_customer_satisfaction: float = Field(default=0.0, description="Average customer satisfaction")
    error_rate: float = Field(default=0.0, description="Error rate percentage")
    avg_confidence_score: float = Field(default=0.0, description="Average confidence score")
    tools_usage: Dict[str, int] = Field(default={}, description="Tool usage counts")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class AgentPerformance(BaseModel):
    """Model for agent performance metrics"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    period_start: datetime = Field(..., description="Performance period start")
    period_end: datetime = Field(..., description="Performance period end")
    metrics: AgentMetrics = Field(..., description="Performance metrics")
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    memory_usage: float = Field(default=0.0, description="Memory usage percentage")
    error_logs: List[Dict[str, Any]] = Field(default=[], description="Error logs during period")
    performance_score: float = Field(default=0.0, description="Overall performance score")

class AgentState(BaseModel):
    """Model representing agent state"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: AgentStatus = Field(..., description="Current agent status")
    current_conversations: List[str] = Field(default=[], description="Active conversation IDs")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    health_check: Dict[str, Any] = Field(default={}, description="Latest health check results")
    current_load: float = Field(default=0.0, description="Current load percentage")
    metadata: Dict[str, Any] = Field(default={}, description="Additional state information")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
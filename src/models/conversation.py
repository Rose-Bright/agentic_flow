from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class Channel(str, Enum):
    WEB = "web"
    PHONE = "phone"
    EMAIL = "email"
    MOBILE = "mobile"
    SOCIAL = "social"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConversationStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ConversationCreate(BaseModel):
    """Model for creating a new conversation"""
    customer_id: str = Field(..., description="Customer identifier")
    channel: Channel = Field(..., description="Communication channel")
    initial_message: str = Field(..., description="Initial customer message")
    priority: Priority = Field(default=Priority.MEDIUM, description="Conversation priority")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class MessageCreate(BaseModel):
    """Model for creating a new message"""
    message: str = Field(..., description="Message content")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=[], description="Message attachments")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class Message(MessageCreate):
    """Model representing a conversation message"""
    id: str = Field(..., description="Message identifier")
    conversation_id: str = Field(..., description="Parent conversation identifier")
    sender_type: str = Field(..., description="Message sender type (customer/agent/system)")
    sender_id: str = Field(..., description="Message sender identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MessageResponse(Message):
    """Model for message response"""
    agent_type: Optional[str] = Field(None, description="Type of agent that processed the message")
    intent: Optional[str] = Field(None, description="Detected message intent")
    confidence: Optional[float] = Field(None, description="Intent classification confidence")
    sentiment: Optional[str] = Field(None, description="Detected message sentiment")
    entities: Optional[List[Dict[str, Any]]] = Field(default=[], description="Extracted entities")

class ConversationResponse(BaseModel):
    """Model for conversation response"""
    id: str = Field(..., description="Conversation identifier")
    customer_id: str = Field(..., description="Customer identifier")
    channel: Channel = Field(..., description="Communication channel")
    status: ConversationStatus = Field(..., description="Current conversation status")
    priority: Priority = Field(..., description="Conversation priority")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    ended_at: Optional[datetime] = Field(None, description="End timestamp if conversation is closed")
    current_agent: Optional[str] = Field(None, description="Current assigned agent")
    previous_agents: List[str] = Field(default=[], description="Previously assigned agents")
    escalation_level: int = Field(default=0, description="Current escalation level")
    resolution_attempts: int = Field(default=0, description="Number of resolution attempts")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    messages: List[MessageResponse] = Field(default=[], description="Conversation messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationMetrics(BaseModel):
    """Model for conversation metrics"""
    total_duration: int = Field(..., description="Total conversation duration in seconds")
    response_time_avg: float = Field(..., description="Average response time in seconds")
    resolution_time: Optional[int] = Field(None, description="Time to resolution in seconds")
    messages_count: int = Field(..., description="Total number of messages")
    customer_messages: int = Field(..., description="Number of customer messages")
    agent_messages: int = Field(..., description="Number of agent messages")
    escalation_count: int = Field(..., description="Number of escalations")
    sentiment_scores: List[float] = Field(default=[], description="Message sentiment scores")
    tools_used: List[str] = Field(default=[], description="Tools used in conversation")
    resolution_successful: Optional[bool] = Field(None, description="Whether resolution was successful")
    customer_satisfaction: Optional[float] = Field(None, description="Customer satisfaction score")
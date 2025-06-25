"""
Database models for the Contact Center system
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
import uuid

from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Boolean, 
    JSON, ForeignKey, Enum as SQLEnum, Float, DECIMAL,
    Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from src.database.connection import Base


class ChannelType(str, enum.Enum):
    """Communication channel types"""
    VOICE = "voice"
    EMAIL = "email"
    CHAT = "chat"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    WHATSAPP = "whatsapp"


class ConversationStatus(str, enum.Enum):
    """Conversation status types"""
    ACTIVE = "active"
    QUEUED = "queued"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"
    ERROR = "error"


class AgentType(str, enum.Enum):
    """Agent types in the system"""
    ROUTING = "routing"
    CUSTOMER_SERVICE = "customer_service"
    TECHNICAL_SUPPORT = "technical_support"
    SALES = "sales"
    BILLING = "billing"
    ESCALATION = "escalation"
    QUALITY_ASSURANCE = "quality_assurance"


class Priority(str, enum.Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CustomerTier(str, enum.Enum):
    """Customer tier levels"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


# LangGraph-specific models
class ConversationCheckpoint(Base):
    """Model for LangGraph conversation checkpoints"""
    __tablename__ = "conversation_checkpoints"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    checkpoint_data: Mapped[str] = mapped_column(Text, nullable=False)
    custom_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_conversation_checkpoints_thread_id", "thread_id"),
        Index("idx_conversation_checkpoints_created_at", "created_at"),
    )


class ConversationWrite(Base):
    """Model for conversation writes/operations"""
    __tablename__ = "conversation_writes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    task_id: Mapped[str] = mapped_column(String(255), nullable=False)
    writes_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_conversation_writes_thread_id", "thread_id"),
        Index("idx_conversation_writes_task_id", "task_id"),
        Index("idx_conversation_writes_created_at", "created_at"),
    )


# Core business models
class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    name = Column(String(255), nullable=False)
    tier = Column(SQLEnum(CustomerTier), default=CustomerTier.BRONZE)
    account_status = Column(String(50), default="active")
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), nullable=True)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    lifetime_value = Column(DECIMAL(10, 2), default=0.0)
    preferences = Column(JSON, default=dict)
    custom_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="customer")
    
    __table_args__ = (
        Index("idx_customers_external_id", "external_id"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_tier", "tier"),
    )


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    channel = Column(SQLEnum(ChannelType), nullable=False)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    subject = Column(String(500), nullable=True)
    initial_message = Column(Text, nullable=True)
    current_agent = Column(SQLEnum(AgentType), nullable=True)
    thread_id = Column(String(255), unique=True, nullable=True)  # For LangGraph integration
    session_data = Column(JSON, default=dict)
    custom_metadata = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    agent_interactions = relationship("AgentInteraction", back_populates="conversation")
    
    __table_args__ = (
        Index("idx_conversations_customer_id", "customer_id"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_thread_id", "thread_id"),
        Index("idx_conversations_started_at", "started_at"),
    )


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)  # 'customer', 'agent', 'system'
    sender_id = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # 'text', 'image', 'file', etc.
    custom_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_timestamp", "timestamp"),
    )


# Analytics and performance models
class ConversationMetric(Base):
    """Model for conversation metrics and analytics"""
    __tablename__ = "conversation_metrics"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4))
    metric_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    agent_type: Mapped[Optional[str]] = mapped_column(String(100))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_conversation_metrics_conversation_id", "conversation_id"),
        Index("idx_conversation_metrics_type", "metric_type"),
        Index("idx_conversation_metrics_agent_type", "agent_type"),
        Index("idx_conversation_metrics_recorded_at", "recorded_at"),
    )


class AgentPerformanceLog(Base):
    """Model for agent performance tracking"""
    __tablename__ = "agent_performance_log"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    performance_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_agent_performance_log_agent_type", "agent_type"),
        Index("idx_agent_performance_log_conversation_id", "conversation_id"),
        Index("idx_agent_performance_log_timestamp", "timestamp"),
        Index("idx_agent_performance_log_success", "success"),
    )


# Keep the remaining models from the first version
class AgentInteraction(Base):
    """Agent interaction tracking"""
    __tablename__ = "agent_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    action = Column(String(100), nullable=False)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    duration_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    custom_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="agent_interactions")


class AgentConfiguration(Base):
    """Agent configuration model"""
    __tablename__ = "agent_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_type = Column(SQLEnum(AgentType), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_config = Column(JSON, default=dict)
    prompt_template = Column(Text, nullable=True)
    tools = Column(JSON, default=list)  # List of available tools
    escalation_conditions = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KnowledgeBase(Base):
    """Knowledge base entries"""
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    embedding = Column(JSON, nullable=True)  # Vector embedding for similarity search
    source = Column(String(255), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationSummary(Base):
    """Conversation summary and analytics"""
    __tablename__ = "conversation_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    summary = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    satisfaction_score = Column(Float, nullable=True)
    resolution_status = Column(String(50), nullable=True)
    topics = Column(JSON, default=list)
    key_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation")
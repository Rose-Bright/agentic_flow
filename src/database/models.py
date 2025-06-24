"""
Database models for the Contact Center system
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Boolean, 
    JSON, ForeignKey, Enum as SQLEnum, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="customer")


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
    session_data = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    agent_interactions = relationship("AgentInteraction", back_populates="conversation")


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(50), nullable=False)  # 'customer', 'agent', 'system'
    sender_id = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text")  # 'text', 'image', 'file', etc.
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


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
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=func.now())
    
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
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


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
    last_updated = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


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
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation")
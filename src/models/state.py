from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CustomerTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"

class TicketStatus(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    email: str
    phone: str
    tier: CustomerTier
    account_status: str
    registration_date: datetime
    lifetime_value: float
    previous_interactions: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    satisfaction_scores: List[float] = field(default_factory=list)

@dataclass
class Ticket:
    ticket_id: str
    priority: Priority
    category: str
    subcategory: str
    description: str
    created_at: datetime
    updated_at: datetime
    sla_deadline: datetime
    tags: List[str] = field(default_factory=list)

@dataclass
class ConversationTurn:
    timestamp: datetime
    speaker: Literal["customer", "agent", "system"]
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent_type: Optional[str] = None

@dataclass
class ResolutionAttempt:
    agent_type: str
    timestamp: datetime
    actions_taken: List[str]
    tools_used: List[str]
    outcome: str
    confidence: float
    success: bool

@dataclass
class EscalationRecord:
    from_agent: str
    to_agent: str
    timestamp: datetime
    reason: str
    context_transfer: Dict[str, Any]

@dataclass
class AgentState:
    # Core Identifiers
    session_id: str
    conversation_id: str
    
    # Customer & Ticket Information
    customer: Optional[CustomerProfile] = None
    ticket: Optional[Ticket] = None
    
    # Conversation Context
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    current_message: str = ""
    current_intent: str = ""
    intent_confidence: float = 0.0
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 0.0
    
    # Agent Assignment & Routing
    current_agent_type: str = ""
    current_agent_id: str = ""
    agent_queue: str = ""
    escalation_level: int = 0
    previous_agents: List[str] = field(default_factory=list)
    escalation_history: List[EscalationRecord] = field(default_factory=list)
    
    # Resolution Tracking
    resolution_attempts: List[ResolutionAttempt] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    knowledge_articles_referenced: List[str] = field(default_factory=list)
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)
    
    # Status & Control Flow
    status: TicketStatus = TicketStatus.NEW
    next_action: str = ""
    requires_human: bool = False
    should_escalate: bool = False
    confidence_score: float = 0.0
    
    # Business Context
    potential_revenue_impact: float = 0.0
    customer_satisfaction_risk: Literal["low", "medium", "high"] = "low"
    sla_breach_risk: bool = False
    
    # Session Management
    session_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    timeout_minutes: int = 30
    
    # Analytics & Monitoring
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # External System References
    external_ticket_id: Optional[str] = None
    crm_case_id: Optional[str] = None
    billing_account_id: Optional[str] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert state to dictionary representation"""
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "customer": self.customer.__dict__ if self.customer else None,
            "ticket": self.ticket.__dict__ if self.ticket else None,
            "current_message": self.current_message,
            "current_intent": self.current_intent,
            "status": self.status.value,
            "escalation_level": self.escalation_level,
            # Add other fields as needed
        }
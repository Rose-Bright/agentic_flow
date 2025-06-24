"""
Base agent class and interfaces
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import json

from pydantic import BaseModel

from src.core.logging import get_logger
from src.database.models import AgentType, ConversationStatus
from src.cache.redis_client import cache_manager

logger = get_logger(__name__)


class AgentMessage(BaseModel):
    """Message structure for agent communication"""
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()


class AgentResponse(BaseModel):
    """Agent response structure"""
    message: str
    action: Optional[str] = None
    data: Dict[str, Any] = {}
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    confidence: float = 1.0
    next_agent: Optional[AgentType] = None


class ConversationContext(BaseModel):
    """Conversation context shared between agents"""
    conversation_id: str
    customer_id: str
    channel: str
    status: ConversationStatus
    messages: List[Dict[str, Any]] = []
    customer_data: Dict[str, Any] = {}
    session_data: Dict[str, Any] = {}
    current_intent: Optional[str] = None
    sentiment: Optional[str] = None
    priority: str = "medium"
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_type: AgentType, config: Dict[str, Any] = None):
        self.agent_type = agent_type
        self.config = config or {}
        self.name = self.config.get("name", agent_type.value)
        self.description = self.config.get("description", "")
        self.tools = self.config.get("tools", [])
        self.escalation_conditions = self.config.get("escalation_conditions", {})
        
    @abstractmethod
    async def process_message(self, message: AgentMessage, 
                            context: ConversationContext) -> AgentResponse:
        """Process incoming message and return response"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup agent resources"""
        pass
    
    async def should_escalate(self, context: ConversationContext, 
                            response: AgentResponse) -> bool:
        """Determine if conversation should be escalated"""
        
        # Check confidence threshold
        min_confidence = self.escalation_conditions.get("min_confidence", 0.5)
        if response.confidence < min_confidence:
            return True
        
        # Check conversation length
        max_messages = self.escalation_conditions.get("max_messages", 10)
        if len(context.messages) > max_messages:
            return True
        
        # Check for specific keywords
        escalation_keywords = self.escalation_conditions.get("keywords", [])
        for keyword in escalation_keywords:
            if keyword.lower() in response.message.lower():
                return True
                
        # Check sentiment
        if context.sentiment == "negative" and len(context.messages) > 3:
            return True
            
        return response.should_escalate
    
    async def update_context(self, context: ConversationContext, 
                           response: AgentResponse) -> ConversationContext:
        """Update conversation context after processing"""
        
        # Add agent response to messages
        context.messages.append({
            "role": "agent",
            "agent_type": self.agent_type.value,
            "content": response.message,
            "timestamp": datetime.now().isoformat(),
            "metadata": response.data
        })
        
        # Update session data
        if response.data:
            context.session_data.update(response.data)
        
        # Update metadata
        context.metadata[f"last_{self.agent_type.value}_response"] = {
            "timestamp": datetime.now().isoformat(),
            "confidence": response.confidence,
            "action": response.action
        }
        
        return context
    
    async def load_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Load conversation context from cache"""
        context_data = await cache_manager.get_conversation_context(conversation_id)
        if context_data:
            try:
                return ConversationContext(**context_data)
            except Exception as e:
                logger.error(f"Failed to load context for conversation {conversation_id}: {e}")
        return None
    
    async def save_context(self, context: ConversationContext) -> None:
        """Save conversation context to cache"""
        try:
            await cache_manager.set_conversation_context(
                context.conversation_id, 
                context.dict()
            )
        except Exception as e:
            logger.error(f"Failed to save context for conversation {context.conversation_id}: {e}")
    
    async def get_agent_state(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific state from cache"""
        state = await cache_manager.get_agent_state(
            conversation_id, 
            self.agent_type.value
        )
        return state or {}
    
    async def save_agent_state(self, conversation_id: str, 
                             state: Dict[str, Any]) -> None:
        """Save agent-specific state to cache"""
        await cache_manager.set_agent_state(
            conversation_id, 
            self.agent_type.value, 
            state
        )


class AgentOrchestrator:
    """Orchestrates communication between different agents"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.routing_rules: Dict[str, AgentType] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator"""
        self.agents[agent.agent_type] = agent
        logger.info(f"Registered agent: {agent.agent_type.value}")
    
    def set_routing_rules(self, rules: Dict[str, AgentType]) -> None:
        """Set routing rules for intent-based agent selection"""
        self.routing_rules = rules
    
    async def route_message(self, message: AgentMessage, 
                          context: ConversationContext) -> AgentType:
        """Route message to appropriate agent based on context"""
        
        # If there's a current agent and no escalation needed, continue with it
        if context.current_intent and not message.metadata.get("force_routing"):
            for intent, agent_type in self.routing_rules.items():
                if intent in context.current_intent:
                    return agent_type
        
        # Default routing logic
        if not context.messages:
            return AgentType.ROUTING
        
        # Check for specific intents in the message
        message_lower = message.content.lower()
        
        if any(word in message_lower for word in ["technical", "not working", "error", "bug"]):
            return AgentType.TECHNICAL_SUPPORT
        elif any(word in message_lower for word in ["billing", "payment", "invoice", "charge"]):
            return AgentType.BILLING
        elif any(word in message_lower for word in ["buy", "purchase", "pricing", "upgrade"]):
            return AgentType.SALES
        elif any(word in message_lower for word in ["complaint", "manager", "escalate"]):
            return AgentType.ESCALATION
        else:
            return AgentType.CUSTOMER_SERVICE
    
    async def process_conversation(self, message: AgentMessage, 
                                 context: ConversationContext) -> AgentResponse:
        """Process conversation through appropriate agent"""
        
        # Route to appropriate agent
        target_agent_type = await self.route_message(message, context)
        
        if target_agent_type not in self.agents:
            logger.error(f"Agent {target_agent_type} not registered")
            return AgentResponse(
                message="I'm sorry, but I'm unable to process your request right now. Please try again later.",
                should_escalate=True,
                escalation_reason="Agent not available"
            )
        
        # Get the agent
        agent = self.agents[target_agent_type]
        
        try:
            # Process message
            response = await agent.process_message(message, context)
            
            # Update context
            updated_context = await agent.update_context(context, response)
            
            # Save updated context
            await agent.save_context(updated_context)
            
            # Check for escalation
            if await agent.should_escalate(updated_context, response):
                response.should_escalate = True
                response.next_agent = self._get_escalation_agent(target_agent_type)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message with agent {target_agent_type}: {e}")
            return AgentResponse(
                message="I encountered an error while processing your request. Let me transfer you to a human agent.",
                should_escalate=True,
                escalation_reason=f"Processing error: {str(e)}"
            )
    
    def _get_escalation_agent(self, current_agent: AgentType) -> AgentType:
        """Get appropriate escalation agent"""
        escalation_map = {
            AgentType.ROUTING: AgentType.CUSTOMER_SERVICE,
            AgentType.CUSTOMER_SERVICE: AgentType.ESCALATION,
            AgentType.TECHNICAL_SUPPORT: AgentType.ESCALATION,
            AgentType.SALES: AgentType.CUSTOMER_SERVICE,
            AgentType.BILLING: AgentType.ESCALATION,
        }
        return escalation_map.get(current_agent, AgentType.ESCALATION)
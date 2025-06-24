from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from src.models.state import (
    AgentState, 
    Priority,
    CustomerTier,
    Sentiment,
    TicketStatus,
    CustomerProfile,
    Ticket,
    ConversationTurn,
    ResolutionAttempt,
    EscalationRecord
)

class AgentType(Enum):
    INTENT_CLASSIFIER = "intent_classifier"
    TIER1 = "tier1_support"
    TIER2 = "tier2_technical"
    TIER3 = "tier3_expert"
    SALES = "sales_agent"
    BILLING = "billing_agent"
    SUPERVISOR = "supervisor_agent"

class AgentOrchestrator:
    """Main orchestrator for the Contact Center Agentic Flow System"""
    
    def __init__(self):
        self.agents: Dict[AgentType, Any] = {}
        self.state_manager = StateManager()
        self.router = AgentRouter()
        self.tool_registry = ToolRegistry()
        self.monitor = PerformanceMonitor()
    
    async def initialize_agents(self):
        """Initialize all agent types with their specific configurations"""
        self.agents = {
            AgentType.INTENT_CLASSIFIER: await self._create_intent_classifier(),
            AgentType.TIER1: await self._create_tier1_agent(),
            AgentType.TIER2: await self._create_tier2_agent(),
            AgentType.TIER3: await self._create_tier3_agent(),
            AgentType.SALES: await self._create_sales_agent(),
            AgentType.BILLING: await self._create_billing_agent(),
            AgentType.SUPERVISOR: await self._create_supervisor_agent()
        }

    async def handle_conversation(self, customer_input: str, conversation_id: str = None) -> AgentState:
        """Handle a new message in the conversation flow"""
        try:
            # Get or create conversation state
            state = await self.state_manager.get_or_create_state(conversation_id)
            
            # Update state with new message
            state.current_message = customer_input
            state.last_activity = datetime.utcnow()
            
            # If new conversation, get customer context
            if not state.customer:
                state.customer = await self._get_customer_context(conversation_id)
            
            # Classify intent if needed
            if not state.current_intent or self._should_reclassify_intent(state):
                intent_result = await self.agents[AgentType.INTENT_CLASSIFIER].classify(
                    customer_input,
                    state
                )
                state.current_intent = intent_result.intent
                state.intent_confidence = intent_result.confidence
            
            # Determine appropriate agent
            target_agent_type = await self.router.determine_agent(state)
            
            # Execute agent logic
            response = await self.agents[target_agent_type].handle_message(
                customer_input,
                state
            )
            
            # Update state with agent response
            state = await self._update_state_with_response(state, response, target_agent_type)
            
            # Check for escalation needs
            if await self._should_escalate(state):
                state = await self._handle_escalation(state)
            
            # Monitor and log performance
            await self.monitor.log_interaction(state)
            
            return state
            
        except Exception as e:
            await self._handle_error(e, state)
            raise
    
    async def _create_intent_classifier(self):
        """Create intent classification agent with Gemini Pro"""
        return IntentClassificationAgent(
            model="gemini-pro",
            confidence_threshold=0.85,
            supported_intents=[
                "account_access",
                "technical_support",
                "billing_inquiry",
                "sales_inquiry",
                "complaint",
                "cancellation",
                "general_inquiry"
            ],
            tools=[
                self.tool_registry.get_tool("get_customer_profile"),
                self.tool_registry.get_tool("search_knowledge_base"),
                self.tool_registry.get_tool("log_interaction_metrics")
            ]
        )
    
    async def _create_tier1_agent(self):
        """Create Tier 1 support agent"""
        return Tier1SupportAgent(
            model="gemini-pro",
            capabilities=[
                "faq_resolution",
                "basic_troubleshooting",
                "account_information",
                "password_reset",
                "service_status"
            ],
            tools=[
                self.tool_registry.get_tool("get_customer_profile"),
                self.tool_registry.get_tool("get_account_services"),
                self.tool_registry.get_tool("search_knowledge_base"),
                self.tool_registry.get_tool("get_troubleshooting_guide"),
                self.tool_registry.get_tool("update_ticket_status"),
                self.tool_registry.get_tool("send_customer_notification")
            ],
            escalation_threshold=0.7
        )
    
    async def _should_escalate(self, state: AgentState) -> bool:
        """Determine if conversation should be escalated"""
        escalation_triggers = {
            "failed_attempts": len(state.resolution_attempts) >= 3,
            "customer_request": "escalate" in state.current_message.lower(),
            "low_confidence": state.confidence_score < 0.7,
            "high_priority": state.ticket and state.ticket.priority == Priority.HIGH,
            "negative_sentiment": state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED],
            "sla_risk": state.sla_breach_risk,
            "vip_customer": state.customer and state.customer.tier == CustomerTier.PLATINUM
        }
        
        return any(escalation_triggers.values())
    
    async def _handle_escalation(self, state: AgentState) -> AgentState:
        """Handle conversation escalation"""
        # Determine escalation level
        current_level = state.escalation_level
        next_level = await self.router.determine_escalation_level(state)
        
        # Create escalation record
        escalation = EscalationRecord(
            from_agent=state.current_agent_type,
            to_agent=next_level,
            timestamp=datetime.utcnow(),
            reason=await self._determine_escalation_reason(state),
            context_transfer=await self._prepare_context_transfer(state)
        )
        
        # Update state
        state.escalation_level += 1
        state.escalation_history.append(escalation)
        state.previous_agents.append(state.current_agent_type)
        state.current_agent_type = next_level
        
        # Notify relevant parties
        await self._notify_escalation(state, escalation)
        
        return state
    
    async def _update_state_with_response(
        self, 
        state: AgentState,
        response: Dict[str, Any],
        agent_type: AgentType
    ) -> AgentState:
        """Update conversation state with agent response"""
        # Add conversation turn
        state.conversation_history.append(
            ConversationTurn(
                timestamp=datetime.utcnow(),
                speaker="agent",
                message=response["message"],
                intent=state.current_intent,
                confidence=response.get("confidence", 0.0),
                agent_type=agent_type.value
            )
        )
        
        # Update resolution attempts if applicable
        if "resolution_attempt" in response:
            state.resolution_attempts.append(
                ResolutionAttempt(
                    agent_type=agent_type.value,
                    timestamp=datetime.utcnow(),
                    actions_taken=response["actions_taken"],
                    tools_used=response["tools_used"],
                    outcome=response["outcome"],
                    confidence=response["confidence"],
                    success=response["success"]
                )
            )
        
        # Update status and metrics
        state.status = response.get("new_status", state.status)
        state.confidence_score = response.get("confidence", state.confidence_score)
        state.customer_satisfaction_risk = response.get(
            "satisfaction_risk",
            state.customer_satisfaction_risk
        )
        
        # Update tools used
        if "tools_used" in response:
            state.tools_used.extend(response["tools_used"])
        
        return state

    async def _handle_error(self, error: Exception, state: Optional[AgentState] = None):
        """Handle and log errors in conversation flow"""
        if state:
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "conversation_id": state.conversation_id,
                "current_state": state.dict()
            }
            state.error_log.append(error_log)
            
            # Update state to reflect error
            state.status = TicketStatus.ESCALATED
            state.should_escalate = True
            
            # Log error for monitoring
            await self.monitor.log_error(error_log)